"""Generate a synthetic credit-card transactions dataset matching the IBM
Kaggle schema. Used as a local fallback so all SQL can be tested without
pulling the 24M-row file.

Output:
    data/raw/transactions.csv
    data/raw/users.csv
    data/raw/cards.csv

Rows: ~500K transactions, 5K users, 12K cards, 36 months.
"""
from __future__ import annotations

import csv
import os
import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_USERS = 5_000
N_CARDS = 12_000
N_TX = 500_000
START = date(2023, 1, 1)
END = date(2025, 12, 31)
DAYS = (END - START).days

STATES = [
    ("CA", 0.13), ("TX", 0.09), ("NY", 0.07), ("FL", 0.07), ("IL", 0.05),
    ("PA", 0.04), ("OH", 0.04), ("GA", 0.04), ("NC", 0.03), ("MI", 0.03),
    ("NJ", 0.03), ("VA", 0.03), ("WA", 0.03), ("AZ", 0.03), ("MA", 0.02),
    ("TN", 0.02), ("IN", 0.02), ("MO", 0.02), ("MD", 0.02), ("WI", 0.02),
    ("CO", 0.02), ("MN", 0.02), ("SC", 0.02), ("AL", 0.02), ("LA", 0.02),
    ("KY", 0.01), ("OR", 0.01), ("OK", 0.01), ("CT", 0.01), ("UT", 0.01),
]
STATE_NAMES, STATE_W = zip(*STATES)
STATE_W = np.array(STATE_W) / sum(STATE_W)

# MCC -> (label, weight, mean ticket, std ticket)
MCCS = {
    5411: ("Grocery Stores", 0.18, 65, 35),
    5812: ("Restaurants", 0.14, 38, 22),
    5814: ("Fast Food", 0.10, 14, 8),
    5541: ("Gas Stations", 0.09, 45, 18),
    5311: ("Department Stores", 0.05, 85, 60),
    5912: ("Drug Stores", 0.05, 28, 18),
    5942: ("Bookstores", 0.01, 32, 20),
    5732: ("Electronics", 0.03, 220, 180),
    5651: ("Apparel", 0.05, 78, 55),
    4111: ("Transit", 0.04, 12, 8),
    4121: ("Taxis/Rideshare", 0.04, 22, 14),
    4511: ("Airlines", 0.02, 380, 220),
    7011: ("Hotels", 0.03, 240, 160),
    5999: ("Misc Retail", 0.06, 55, 40),
    5921: ("Liquor Stores", 0.02, 42, 28),
    7832: ("Movie Theaters", 0.01, 24, 12),
    7997: ("Gyms/Clubs", 0.01, 48, 22),
    5734: ("Software/Subscriptions", 0.02, 18, 14),
    8011: ("Medical/Doctors", 0.02, 145, 110),
    5200: ("Home Improvement", 0.03, 95, 80),
}
MCC_CODES = list(MCCS.keys())
MCC_W = np.array([MCCS[m][1] for m in MCC_CODES])
MCC_W = MCC_W / MCC_W.sum()

CITIES_BY_STATE = {
    "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose"],
    "TX": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
    "NY": ["New York", "Buffalo", "Rochester", "Albany"],
    "FL": ["Miami", "Orlando", "Tampa", "Jacksonville"],
}
DEFAULT_CITIES = ["Springfield", "Franklin", "Riverside", "Madison", "Georgetown"]


def merchant_pool(n: int = 4000) -> list[tuple[str, int, str, str, str]]:
    """Pre-generate a stable pool of merchants. (name, mcc, city, state, zip)."""
    pool = []
    brands = [
        "Walmart", "Target", "Costco", "Kroger", "Safeway", "Whole Foods",
        "Trader Joes", "Publix", "Aldi", "HEB", "Wegmans", "Albertsons",
        "McDonalds", "Starbucks", "Chipotle", "Subway", "Chick-fil-A",
        "Taco Bell", "Wendys", "Panera", "Dunkin", "Shell", "Exxon",
        "Chevron", "BP", "Mobil", "CVS", "Walgreens", "Rite Aid",
        "Amazon", "Best Buy", "Apple Store", "Home Depot", "Lowes",
        "Macys", "Nordstrom", "Gap", "Nike", "Uber", "Lyft",
        "Delta", "United", "American Airlines", "Marriott", "Hilton",
        "Hyatt", "Netflix", "Spotify", "Adobe", "Microsoft",
    ]
    for i in range(n):
        mcc = int(np.random.choice(MCC_CODES, p=MCC_W))
        # branded for common categories, generic otherwise
        if random.random() < 0.35:
            name = f"{random.choice(brands)} #{random.randint(100, 9999)}"
        else:
            name = f"{MCCS[mcc][0].split()[0]} Merchant {i:05d}"
        state = np.random.choice(STATE_NAMES, p=STATE_W)
        city = random.choice(CITIES_BY_STATE.get(state, DEFAULT_CITIES))
        zip_code = f"{random.randint(10000, 99999)}"
        pool.append((name, mcc, city, state, zip_code))
    return pool


def write_users() -> None:
    path = RAW / "users.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "user_id", "signup_date", "birth_year", "gender", "state",
            "yearly_income", "credit_score"
        ])
        for uid in range(N_USERS):
            signup = START + timedelta(days=random.randint(-720, DAYS - 30))
            birth_year = random.randint(1945, 2003)
            gender = random.choice(["M", "F"])
            state = np.random.choice(STATE_NAMES, p=STATE_W)
            income = int(np.clip(np.random.lognormal(11.0, 0.5), 20000, 400000))
            score = int(np.clip(np.random.normal(710, 70), 480, 850))
            w.writerow([uid, signup.isoformat(), birth_year, gender, state, income, score])
    print(f"wrote {path} ({N_USERS} rows)")


def write_cards() -> tuple[list[int], list[int]]:
    """Returns (card_ids, card_user_ids) aligned by index."""
    path = RAW / "cards.csv"
    card_ids = []
    card_users = []
    # most users get 1-2 cards, ~10% get 3-5 (multi-card cohort)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "card_id", "user_id", "card_brand", "card_type", "issue_date",
            "expires", "has_chip"
        ])
        cid = 0
        for uid in range(N_USERS):
            r = random.random()
            n = 5 if r < 0.03 else 3 if r < 0.10 else 2 if r < 0.45 else 1
            for _ in range(n):
                if cid >= N_CARDS:
                    break
                brand = random.choice(["Visa", "Mastercard", "Amex", "Discover"])
                ctype = random.choice(["Credit", "Debit"])
                issue = START + timedelta(days=random.randint(-900, DAYS - 60))
                expires = issue + timedelta(days=365 * random.randint(3, 5))
                has_chip = random.random() < 0.92
                w.writerow([cid, uid, brand, ctype, issue.isoformat(),
                            expires.isoformat(), "YES" if has_chip else "NO"])
                card_ids.append(cid)
                card_users.append(uid)
                cid += 1
            if cid >= N_CARDS:
                break
    print(f"wrote {path} ({len(card_ids)} rows)")
    return card_ids, card_users


def write_transactions(card_ids: list[int], card_users: list[int]) -> None:
    path = RAW / "transactions.csv"
    n_cards = len(card_ids)
    # card activity weight — long-tail (some cards used heavily, many lightly)
    activity = np.random.gamma(1.5, 1.0, size=n_cards)
    activity = activity / activity.sum()

    merchants = merchant_pool()
    n_merch = len(merchants)
    # merchant popularity — pareto-ish
    m_weights = np.random.gamma(0.8, 1.0, size=n_merch)
    m_weights = m_weights / m_weights.sum()

    error_codes = ["", "", "", "", "", "", "", "", "", "",  # mostly ok
                   "Insufficient Balance", "Bad PIN", "Technical Glitch",
                   "Bad Card Number", "Bad Expiration", "Bad CVV"]

    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "user_id", "card_id", "year", "month", "day", "time", "amount",
            "use_chip", "merchant_name", "merchant_city", "merchant_state",
            "zip", "mcc", "errors", "is_fraud"
        ])
        # pre-sample for speed
        card_pick = np.random.choice(n_cards, size=N_TX, p=activity)
        merch_pick = np.random.choice(n_merch, size=N_TX, p=m_weights)
        # date drift — more activity recent months (mild growth)
        day_offsets = np.random.beta(2.2, 1.6, size=N_TX) * DAYS
        day_offsets = day_offsets.astype(int)

        for i in range(N_TX):
            ci = int(card_pick[i])
            cid = card_ids[ci]
            uid = card_users[ci]
            mi = int(merch_pick[i])
            mname, mcc, mcity, mstate, mzip = merchants[mi]
            _, _, mean_amt, std_amt = MCCS[mcc]
            amt = max(0.5, np.random.normal(mean_amt, std_amt))
            d = START + timedelta(days=int(day_offsets[i]))
            hh = random.randint(0, 23)
            mm = random.randint(0, 59)
            err = random.choice(error_codes)
            # fraud rare; slightly biased toward high-ticket categories
            fraud_p = 0.004 + (0.01 if mcc in (5732, 4511, 7011, 5311) else 0)
            is_fraud = "Yes" if random.random() < fraud_p else "No"
            w.writerow([
                uid, cid, d.year, d.month, d.day, f"{hh:02d}:{mm:02d}",
                f"${amt:.2f}", "Chip Transaction" if random.random() < 0.78 else "Swipe Transaction",
                mname, mcity, mstate, mzip, mcc, err, is_fraud,
            ])
            if i % 100_000 == 0 and i:
                print(f"  ...{i:,} tx written")
    print(f"wrote {path} ({N_TX} rows)")


def main() -> None:
    write_users()
    card_ids, card_users = write_cards()
    write_transactions(card_ids, card_users)
    print("done.")


if __name__ == "__main__":
    main()
