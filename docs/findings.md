# QBR Findings — Credit Card Portfolio

Findings from running the queries in [`/sql`](../sql/) against the
**real IBM Credit Card Transactions dataset** (Ealtman 2019 on Kaggle):
**24.4M transactions, 2,000 cardholders, 6,146 cards, 1991 – Feb 2020**.
Framing: what an analyst on a financial institution partnership team
would surface to the account team ahead of a QBR.

The full per-query CSV outputs sit in
[`/data/processed/query_outputs/`](../data/processed/query_outputs/).

---

## 1. Portfolio finished 2019 at a $72M annualized run-rate, with Jan 2020 up +16% YoY

December 2019 closed at **$6.08M** in approved monthly volume; January
2020 jumped to **$7.08M** — a **+16.4% YoY** lift and the largest single
MoM gain in the trailing 12 months (Q1.1, Q1.4). February eased back to
$6.76M (still **+22.4% YoY**).

**Why it matters.** Two strong months back-to-back to start 2020 should
be the headline of the QBR — the portfolio is accelerating into the new
year, not coasting on 2019 momentum.

**Suggested next step.** Cut the January growth by acquisition cohort
to isolate new-card activations from existing-cohort lift. If new
cohorts drove most of the +16%, the team should lean into the
acquisition channel that produced them.

---

## 2. Active-card rate is near-saturated at ~100%

Active card rate (cards with ≥1 approved tx / eligible cards) has run
between **99.5% and 100%** for the last twelve months (Q1.2). This is
a near-universally-engaged book.

**Why it matters.** This portfolio has effectively no activation
problem. Future growth has to come from per-card spend, not from
waking up dormant plastic.

**Suggested next step.** Shift KPI focus from "active card rate" (which
is at ceiling) to "high-engagement cards" — defined e.g. as cards with
≥10 transactions and ≥$500 spend per month — so the team has a metric
that can still move.

---

## 3. Money Transfer is the surprise #1 category at 10.4% of portfolio spend

The top three categories by approved volume are:
**Money Transfer $98.6M (10.4%)**, **Grocery Stores $73.5M (7.8%)**,
**Wholesale Clubs $68.8M (7.3%)** (Q2.1). Money Transfer and Utilities
combined account for **15.8%** of spend — a much larger share than a
typical issuer would assume.

**Why it matters.** Money Transfer (MCC 4829) usually carries lower
interchange than retail spend, so a high volume share there
under-monetizes vs. its volume rank. Pricing and rewards strategy
should be modeled on category mix, not just total volume.

**Suggested next step.** Build a weighted-interchange estimate per
category (volume × category-typical interchange rate) and re-rank the
top 10 by revenue contribution. The list will look very different.

---

## 4. Spend is highly concentrated: top 10% of users drive 31.7% of volume

The top decile of spenders accounts for **$329M / 31.7%** of approved
lifetime volume, with an average spend of **$1.65M per user**. The
bottom 50% of users contribute just **15.4%** of volume (Q3.2). The
distribution is more skewed than 80/20.

**Why it matters.** Losing the top decile would cost roughly a third
of the portfolio. These 200 cardholders are the relationship-management
priority list and the single biggest source of churn risk.

**Suggested next step.** Build a churn-risk score on the top decile
specifically (90-day drop in monthly transactions, category mix shift
away from anchor categories) and route flagged users to retention
outreach within 30 days of a flag.

---

## 5. Multi-card users spend ~3x what single-card users spend

Single-card users average **$265K** in lifetime approved spend; users
with 5+ cards average **$822K** (Q3.3). The 3–4 card cohort
($578K avg) is the single largest segment by both count (825 users)
and total contribution ($477M / 46% of total volume).

**Why it matters.** Cross-sell directly correlates with portfolio
value. Even moving a single-card user to two cards ~1.4x'es lifetime
spend ($265K → $383K).

**Suggested next step.** Identify the top quartile of single-card
spenders with ≥5 years of tenure and high category diversity — that
cohort has the highest probability of accepting a second-card offer.

---

## 6. Top-5-state concentration is 38.6% — well within tolerance

CA leads at **12.2%** of volume, followed by TX (8.1%), NY (7.5%),
FL (6.7%), PA (4.0%). Cumulative top-5 share: **38.6%** (Q4.3).
Cumulative top-10 share: **55.4%**.

**Why it matters.** Comfortably below the ~50% top-5 concentration
threshold that would trigger a concentration-risk flag. The portfolio
is well-diversified geographically.

**Suggested next step.** Maintain. If targeted-acquisition spend is
ever redirected to a specific state (e.g. a regional bank co-brand),
re-check this distribution annually so the concentration doesn't drift
above 50%.

---

## 7. Online-channel fraud is concentrated in a handful of categories

Looking at fraud volume by category × channel (Q4.2), the highest-loss
combinations are all **online**: Department Stores online ($347K
fraud volume, 1.6% fraud rate), Cruises online ($329K, 50% rate),
Wholesale Clubs online, Money Transfer online. In contrast, in-person
chip transactions show fraud rates **below 0.1%** across categories.

**Why it matters.** This is a classic card-not-present (CNP) fraud
profile — physical-presence categories are safe; online checkout is
where the loss happens. Investing in 3DS / step-up auth on CNP traffic
in these categories would attack the bulk of fraud loss.

**Suggested next step.** Pilot 3DS on online Department Stores and
Electronics transactions above $50 ticket size; measure (a) decline
in fraud rate, (b) false-positive lift in legitimate-decline rate, and
(c) abandonment rate at checkout, over a 60-day window.

---

## 8. Per-active-user engagement is exceptional: ~90 transactions/month

Average transactions per active user per month has held between **85
and 95** for the last twelve months (Q3.4); median is in the low 80s.
These are heavy daily users.

**Why it matters.** The engagement bar here is materially higher than
a typical issuer book (industry median is closer to 15–25 tx/month).
Reinforces that this isn't a portfolio where engagement is the lever
— growth has to come from cardholder acquisition or basket size.

**Suggested next step.** Avoid spending on engagement-stimulation
campaigns (already saturated). Reallocate that budget to top-decile
retention (finding #4) and to acquisition channels that produced the
January 2020 lift (finding #1).

---

*Numbers above were generated by running each query in
[`/sql`](../sql/) against the real IBM dataset loaded into the local
DuckDB warehouse. The same SQL ports to BigQuery with the dialect
notes in [`methodology.md`](methodology.md).*
