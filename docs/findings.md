# QBR Findings — Credit Card Portfolio

Findings from running the queries in [`/sql`](../sql/) against the loaded
transaction set (500K transactions, 5,000 users, ~8,000 cards, Jan 2023 –
Dec 2025). Framing: what a junior analyst on a financial institution
partnership team would surface to the account team ahead of a QBR.

The full per-query CSV outputs sit in
[`/data/processed/query_outputs/`](../data/processed/query_outputs/).

---

## 1. Volume more than doubled YoY in 2024 before plateauing in 2025

Approved spend grew from **$3.7M** (FY2023) to **$9.6M** (FY2024) —
a **161% YoY** lift driven mostly by ramp, not basket inflation.
2025 H1 then plateaued at roughly **$830K/month** before softening into
H2 (Q1.1, Q1.4).

**Why it matters.** The partnership team should set 2026 targets off the
2025 H1 run-rate (~$10M annualized), not the 2024 growth curve, which
was acquisition-driven and isn't repeatable.

**Suggested next step.** Pull a top-down 2026 plan that holds active
cards flat and only models spend-per-active-card growth. Anything above
that is upside.

---

## 2. Active-card rate has been falling since the late-2024 peak

Active-card rate (cards with ≥1 approved tx / eligible cards) peaked at
**95.4%** in Aug 2024 and has drifted down to **~89%** through 2025 H1
(Q1.2). Volume held up over the same window only because the eligible
card base grew.

**Why it matters.** That's classic "activation softening" — new cards
are being issued, but a growing share aren't being used. Every inactive
card is a write-off on acquisition cost.

**Suggested next step.** Cut active rate by issue-date cohort to see
whether recent vintages are activating worse than older ones, and align
with marketing on whether the welcome-bonus flow has changed.

---

## 3. Grocery is the #1 category at 19% of spend but Airlines + Hotels
   are 23% combined

Top 3 by approved volume: **Grocery Stores $4.0M (19.2%)**,
**Airlines $2.8M (13.5%)**, **Hotels $2.0M (9.3%)** (Q2.1). Average
ticket: grocery ~$65, airlines ~$380, hotels ~$240 (Q2.3) — different
businesses entirely.

**Why it matters.** Grocery is the everyday-spend anchor; travel is the
high-margin, low-frequency premium category. Reward structure and
fraud-rule tuning should be designed for both, not optimized for one.

**Suggested next step.** Quantify interchange revenue by category (we
can layer in MCC-level rates) so the team can rank categories by
contribution, not just volume.

---

## 4. Spend is concentrated: top 10% of users drive 29% of volume

The top decile of spenders accounts for **$6.2M / 29.3%** of approved
volume, with an average annual spend of **$12,366**. The bottom 50% of
users contribute just **19.3%** of volume (Q3.2).

**Why it matters.** Less concentrated than the canonical 80/20, but
still skewed enough that losing the top decile would put a measurable
dent in interchange. These are the relationship-management priority
list.

**Suggested next step.** Build a churn-risk score on the top decile
specifically (drop in monthly transactions, category mix shift away
from anchor categories) and route flagged users to retention outreach.

---

## 5. Multi-card users spend 5x what single-card users spend

Single-card users average **$2,638** in approved spend; users with 5+
cards average **$13,251** (Q3.3). Multi-card users are 5.9% of the
base but contribute 23.2% of volume.

**Why it matters.** Cross-sell directly correlates with portfolio
value. Even moving a single-card user to two cards roughly doubles
their spend ($2,638 → $5,209).

**Suggested next step.** Identify the top quartile of single-card
spenders with ≥12 months of tenure and high category diversity — that
cohort has the highest probability of accepting a second-card offer.

---

## 6. Top-5-state concentration is 47% — within tolerance, but watch FL

CA leads at **16.6%** of volume, followed by TX (9.1%), FL (7.2%),
NY (6.3%), OH (4.3%). Cumulative top-5 share: **47.9%** (Q4.3).

**Why it matters.** Anything above ~50% is a concentration risk; we're
just under. Florida in particular has high seasonality and disaster
exposure — worth modeling separately.

**Suggested next step.** Stress-test the portfolio against a "Florida
hurricane month" scenario (assume FL volume drops 40% for one month)
to estimate the dollar exposure.

---

## 7. Fraud rate concentrated in high-ticket categories, not in volume drivers

Fraud rate by category: Airlines **1.50%**, Electronics **1.51%**,
Hotels **1.45%**, Department Stores **1.42%** — vs. Grocery at
**0.37%** (Q4.2). High-ticket categories are roughly **4x** the fraud
rate of everyday spend.

**Why it matters.** Fraud losses are dominated by ticket size, not by
attempt count. A single fraudulent airline transaction is the same
loss as ~6 fraudulent grocery transactions.

**Suggested next step.** Tighten step-up auth rules on Airlines/Hotels
above the **$500** mark (which is roughly the p95 ticket for those
categories) and measure the false-positive rate before rolling broader.

---

## 8. Per-active-user engagement is steady — growth has been driven by
   base expansion, not by users transacting more

Average transactions per active user per month has hovered between
**3.0 and 3.4** for all of 2024 and 2025 H1 (Q3.4). Active-user count
grew ~25% YoY over that same window.

**Why it matters.** Reinforces finding #1 — growth has been
acquisition-led, not engagement-led. To grow the portfolio without
more acquisition spend, we need to move per-user engagement.

**Suggested next step.** A/B test a category-bonus offer (e.g.,
groceries) on a holdout of low-frequency active users and measure
incremental transactions over the following 90 days.

---

*Numbers above were generated by running each query in [`/sql`](../sql/)
against the local DuckDB warehouse. The same SQL ports to BigQuery with
the dialect notes in [`methodology.md`](methodology.md).*
