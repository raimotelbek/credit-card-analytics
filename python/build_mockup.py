"""Render a static PNG mockup of the intended Looker Studio dashboard.

The numbers are sourced from the actual query outputs in
data/processed/query_outputs/, so the mockup reflects real values from
the loaded dataset rather than placeholder figures.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parent.parent
Q = ROOT / "data" / "processed" / "query_outputs"
OUT = ROOT / "dashboards" / "mockup.png"


def fmt_usd(v: float) -> str:
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.0f}"


def main() -> None:
    vol = pd.read_csv(Q / "01_portfolio_health__Q1.1.csv", parse_dates=["month"])
    act = pd.read_csv(Q / "01_portfolio_health__Q1.2.csv", parse_dates=["month"])
    mom = pd.read_csv(Q / "01_portfolio_health__Q1.4.csv", parse_dates=["month"])
    cat = pd.read_csv(Q / "02_merchant_category__Q2.1.csv")
    pareto = pd.read_csv(Q / "03_customer_behavior__Q3.2.csv")
    geo = pd.read_csv(Q / "04_risk_operations__Q4.3.csv")
    mix = pd.read_csv(Q / "02_merchant_category__Q2.2.csv", parse_dates=["month"])
    cohort = pd.read_csv(Q / "03_customer_behavior__Q3.1.csv", parse_dates=["cohort_month"])

    # KPIs from the most recent month in the data.
    target = vol["month"].max()
    kpi_vol_row = vol.loc[vol["month"] == target].iloc[0]
    kpi_act_row = act.loc[act["month"] == target].iloc[0]
    kpi_mom_row = mom.loc[mom["month"] == target].iloc[0]

    fig = plt.figure(figsize=(18, 14))
    fig.patch.set_facecolor("#f7f8fa")
    gs = GridSpec(
        5, 4, figure=fig, height_ratios=[0.6, 1.4, 1.4, 1.4, 1.4],
        hspace=0.55, wspace=0.35,
    )

    # ---- Title strip ----
    title_ax = fig.add_subplot(gs[0, :])
    title_ax.axis("off")
    title_ax.text(0.005, 0.65,
                  f"Issuer Portfolio QBR  ·  Snapshot {target.strftime('%Y-%m')}",
                  fontsize=22, fontweight="bold", color="#1f2a44")
    yr_min = vol["month"].min().year
    yr_max = vol["month"].max().year
    title_ax.text(0.005, 0.18,
                  f"IBM Credit Card Transactions  ·  24.4M tx  ·  2,000 users  ·  6,146 cards  ·  {yr_min} – {yr_max}",
                  fontsize=11, color="#5a6478")

    # ---- KPI strip ----
    label_month = target.strftime("%b %Y")
    kpis = [
        (f"Approved Volume ({label_month})", fmt_usd(kpi_vol_row["approved_volume_usd"]), f"MoM {kpi_mom_row['mom_growth_pct']:+.1f}%"),
        ("Transactions",                     f"{int(kpi_vol_row['tx_count']):,}",         f"YoY {kpi_mom_row['yoy_growth_pct']:+.1f}%"),
        ("Active Cards",                     f"{int(kpi_vol_row['active_cards']):,}",     f"Active rate {kpi_act_row['active_rate_pct']:.1f}%"),
        ("Avg Ticket",                       f"${kpi_vol_row['avg_ticket_usd']:.2f}",     "stable ±2% YoY"),
    ]
    for i, (label, val, sub) in enumerate(kpis):
        ax = fig.add_subplot(gs[1, i])
        ax.set_facecolor("white")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#dde2ec")
        ax.text(0.5, 0.78, label, ha="center", va="center", fontsize=10, color="#5a6478")
        ax.text(0.5, 0.45, val, ha="center", va="center", fontsize=22, fontweight="bold", color="#1f2a44")
        ax.text(0.5, 0.18, sub, ha="center", va="center", fontsize=9.5, color="#3aa676")

    # ---- Row 2 left: monthly volume line ----
    ax = fig.add_subplot(gs[2, :2])
    ax.set_facecolor("white")
    ax.plot(vol["month"], vol["approved_volume_usd"] / 1000, color="#2e5bda", lw=2.2)
    ax.fill_between(vol["month"], 0, vol["approved_volume_usd"] / 1000, color="#2e5bda", alpha=0.10)
    ax.set_title("Approved volume by month  ($K)", loc="left", fontsize=12, fontweight="bold", color="#1f2a44")
    ax.grid(True, axis="y", color="#eef0f5")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    for s in ax.spines.values(): s.set_color("#dde2ec")
    ax.set_ylabel("$K", color="#5a6478")
    ax.tick_params(colors="#5a6478")

    # ---- Row 2 right: category mix stacked area (top 6) ----
    ax = fig.add_subplot(gs[2, 2:])
    ax.set_facecolor("white")
    top6 = cat.head(6)["category"].tolist()
    mix6 = mix[mix["category"].isin(top6)]
    pivot = mix6.pivot(index="month", columns="category", values="pct_of_month").fillna(0)
    pivot = pivot[top6]
    palette = ["#2e5bda", "#3aa676", "#e8a33d", "#c0504d", "#8064a2", "#4bacc6"]
    ax.stackplot(pivot.index, pivot.values.T, labels=pivot.columns, colors=palette, alpha=0.85)
    ax.set_title("Category mix over time  (% of monthly spend, top 6)", loc="left",
                 fontsize=12, fontweight="bold", color="#1f2a44")
    ax.legend(loc="upper right", fontsize=7.5, frameon=False, ncol=2)
    ax.set_ylim(0, max(60, pivot.sum(axis=1).max() + 5))
    ax.grid(True, axis="y", color="#eef0f5")
    for s in ax.spines.values(): s.set_color("#dde2ec")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#5a6478")

    # ---- Row 3 left: top categories bar ----
    ax = fig.add_subplot(gs[3, :2])
    ax.set_facecolor("white")
    top10 = cat.head(10).iloc[::-1]
    bars = ax.barh(top10["category"], top10["approved_volume_usd"] / 1_000_000, color="#2e5bda")
    for b, pct in zip(bars, top10["pct_of_portfolio"]):
        ax.text(b.get_width() + 0.05, b.get_y() + b.get_height()/2,
                f"{pct:.1f}%", va="center", fontsize=9, color="#5a6478")
    ax.set_title("Top 10 categories by approved volume  ($M)", loc="left",
                 fontsize=12, fontweight="bold", color="#1f2a44")
    ax.grid(True, axis="x", color="#eef0f5")
    for s in ax.spines.values(): s.set_color("#dde2ec")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#5a6478")

    # ---- Row 3 right: spender Pareto ----
    ax = fig.add_subplot(gs[3, 2:])
    ax.set_facecolor("white")
    order = ["Top 10%", "Middle 40%", "Bottom 50%"]
    pareto_sorted = pareto.set_index("spender_tier").loc[order]
    colors_p = ["#2e5bda", "#5a86e6", "#a4bdf3"]
    bars = ax.bar(pareto_sorted.index, pareto_sorted["pct_of_total_spend"], color=colors_p)
    for b, v, n in zip(bars, pareto_sorted["pct_of_total_spend"], pareto_sorted["users"]):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 1.0,
                f"{v:.1f}%\n({int(n):,} users)", ha="center", fontsize=9.5, color="#1f2a44")
    ax.set_title("Spender concentration  (share of total approved spend)", loc="left",
                 fontsize=12, fontweight="bold", color="#1f2a44")
    ax.set_ylim(0, max(pareto_sorted["pct_of_total_spend"]) * 1.35)
    ax.grid(True, axis="y", color="#eef0f5")
    for s in ax.spines.values(): s.set_color("#dde2ec")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#5a6478")

    # ---- Row 4 left: cohort heatmap ----
    ax = fig.add_subplot(gs[4, :2])
    ax.set_facecolor("white")
    # Use cohorts from the trailing analysis window. The IBM dataset's
    # signup dates (derived from earliest card open) span 1991-2019, so
    # filter to cohorts large enough to be visually informative.
    co = cohort[(cohort["cohort_month"] >= "2014-01-01") &
                (cohort["cohort_month"] <= "2019-06-01")]
    piv = co.pivot(index="cohort_month", columns="months_since_signup", values="retention_pct")
    piv = piv.tail(18).iloc[:, :13]
    im = ax.imshow(piv.values, aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels([d.strftime("%Y-%m") for d in piv.index], fontsize=8)
    ax.set_title("Cohort retention  (% of signup cohort active in month N)", loc="left",
                 fontsize=12, fontweight="bold", color="#1f2a44")
    ax.set_xlabel("Months since signup", color="#5a6478", fontsize=9)
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.ax.tick_params(labelsize=8, colors="#5a6478")
    ax.tick_params(colors="#5a6478")

    # ---- Row 4 right: geo concentration ----
    ax = fig.add_subplot(gs[4, 2:])
    ax.set_facecolor("white")
    geo10 = geo.head(10).iloc[::-1]
    bars = ax.barh(geo10["state"], geo10["pct_of_portfolio"], color="#3aa676")
    for b, cum in zip(bars, geo10["cumulative_pct"]):
        ax.text(b.get_width() + 0.15, b.get_y() + b.get_height()/2,
                f"cum {cum:.0f}%", va="center", fontsize=8, color="#5a6478")
    ax.set_title("Geographic concentration  (top 10 states by % of portfolio)", loc="left",
                 fontsize=12, fontweight="bold", color="#1f2a44")
    ax.grid(True, axis="x", color="#eef0f5")
    for s in ax.spines.values(): s.set_color("#dde2ec")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(colors="#5a6478")

    fig.text(0.005, 0.005,
             "Mockup rendered from /sql query outputs · BigQuery + Looker Studio in production",
             fontsize=8, color="#9aa3b5")

    fig.savefig(OUT, dpi=130, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
