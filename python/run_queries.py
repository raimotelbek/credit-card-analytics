"""Run every query in /sql against the local DuckDB warehouse and save
results to data/processed/query_outputs/.

The SQL files are written in BigQuery dialect. We translate a small set
of BQ-specific constructs to DuckDB equivalents at run time so a single
file works for both engines:

    DATE_TRUNC(col, MONTH)              -> DATE_TRUNC('month', col)
    DATE_DIFF(a, b, MONTH)              -> DATE_DIFF('month', b, a)
    LAST_DAY(col)                       -> LAST_DAY(col)               (same)
    APPROX_QUANTILES(c, 100)[OFFSET(n)] -> QUANTILE_CONT(c, n/100.0)

These are documented in docs/methodology.md so a BigQuery reviewer can
see exactly what changes (and why nothing structural does).
"""
from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = ROOT / "sql"
OUT_DIR = ROOT / "data" / "processed" / "query_outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = ROOT / "data" / "warehouse.duckdb"


def translate_bq_to_duckdb(sql: str) -> str:
    # DATE_TRUNC(col, GRANULARITY) -> DATE_TRUNC('granularity', col)
    sql = re.sub(
        r"DATE_TRUNC\(\s*([^,()]+?)\s*,\s*(YEAR|QUARTER|MONTH|WEEK|DAY)\s*\)",
        lambda m: f"DATE_TRUNC('{m.group(2).lower()}', {m.group(1).strip()})",
        sql,
        flags=re.IGNORECASE,
    )
    # DATE_DIFF(a, b, MONTH) -> DATE_DIFF('month', b, a)   (BigQuery: a - b;
    # DuckDB: end - start. BigQuery is end - start as well, but DuckDB takes
    # ('part', start, end) — note arg order flip relative to BQ.)
    sql = re.sub(
        r"DATE_DIFF\(\s*([^,()]+?)\s*,\s*([^,()]+?)\s*,\s*(YEAR|QUARTER|MONTH|WEEK|DAY)\s*\)",
        lambda m: f"DATE_DIFF('{m.group(3).lower()}', {m.group(2).strip()}, {m.group(1).strip()})",
        sql,
        flags=re.IGNORECASE,
    )
    # APPROX_QUANTILES(col, 100)[OFFSET(n)] -> QUANTILE_CONT(col, n/100.0)
    sql = re.sub(
        r"APPROX_QUANTILES\(\s*([^,()]+?)\s*,\s*100\s*\)\s*\[\s*OFFSET\(\s*(\d+)\s*\)\s*\]",
        lambda m: f"QUANTILE_CONT({m.group(1).strip()}, {int(m.group(2))/100.0})",
        sql,
        flags=re.IGNORECASE,
    )
    return sql


def split_statements(sql_text: str) -> list[tuple[str, str]]:
    """Split a multi-statement SQL file on `;` while keeping the leading
    comment block as the query's label. Returns [(label, sql), ...].

    Naive split on `;` would break on semicolons inside `-- comments`,
    so we mask comment lines first.
    """
    masked_lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            masked_lines.append(line.replace(";", ","))
        else:
            masked_lines.append(line)
    masked = "\n".join(masked_lines)
    parts = [p.strip() for p in masked.split(";") if p.strip()]
    out: list[tuple[str, str]] = []
    for p in parts:
        # find a Q<n.n> tag in the leading comments
        label_match = re.search(r"Q\d+\.\d+", p)
        label = label_match.group(0) if label_match else f"q{len(out)+1}"
        out.append((label, p))
    return out


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    # default schema so unqualified analytics.x is resolvable; we set search path
    con.execute("SET search_path = 'main';")

    summary_rows = []
    for sql_path in sorted(SQL_DIR.glob("*.sql")):
        if sql_path.name.startswith("00_"):
            continue  # DDL only, BigQuery-side
        print(f"\n=== {sql_path.name} ===")
        text = translate_bq_to_duckdb(sql_path.read_text())
        for label, stmt in split_statements(text):
            try:
                df = con.execute(stmt).fetchdf()
            except Exception as e:
                print(f"  [FAIL] {label}: {e}")
                summary_rows.append({"file": sql_path.name, "query": label,
                                     "rows": 0, "ok": False, "error": str(e)[:200]})
                continue
            out_csv = OUT_DIR / f"{sql_path.stem}__{label}.csv"
            df.to_csv(out_csv, index=False)
            print(f"  [OK]   {label}: {len(df):>6} rows -> {out_csv.name}")
            summary_rows.append({"file": sql_path.name, "query": label,
                                 "rows": len(df), "ok": True, "error": ""})

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "_summary.csv", index=False)
    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
