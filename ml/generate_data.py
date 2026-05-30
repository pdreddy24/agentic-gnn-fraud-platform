from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def generate_synthetic_transactions(n: int = 2500, seed: int = 42) -> pd.DataFrame:
    """Generate relationship-rich fraud data suitable for a small GNN demo.

    This is synthetic data for learning/demo. Replace it with your real data later.
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    users = [f"U{i:04d}" for i in range(1, 501)]
    devices = [f"D{i:04d}" for i in range(1, 181)]
    cards = [f"C{i:04d}" for i in range(1, 650)]
    ips = [f"IP{i:04d}" for i in range(1, 260)]
    merchants = [f"M{i:04d}" for i in range(1, 90)]
    channels = ["web", "mobile", "pos"]
    countries = ["US", "IN", "GB", "CA", "NG", "BR", "RU"]

    risky_devices = set(rng.choice(devices, 18, replace=False))
    risky_ips = set(rng.choice(ips, 25, replace=False))
    risky_merchants = set(rng.choice(merchants, 12, replace=False))
    risky_users = set(rng.choice(users, 35, replace=False))

    start = datetime(2026, 1, 1, 0, 0, 0)
    rows = []

    # A few devices/IPs are shared by many users to simulate fraud rings.
    ring_devices = list(rng.choice(list(risky_devices), 5, replace=False))
    ring_ips = list(rng.choice(list(risky_ips), 7, replace=False))

    for i in range(n):
        user = random.choice(users)
        if user in risky_users and rng.random() < 0.55:
            device = random.choice(ring_devices)
            ip = random.choice(ring_ips)
            merchant = random.choice(list(risky_merchants))
        else:
            device = random.choice(devices)
            ip = random.choice(ips)
            merchant = random.choice(merchants)

        card = random.choice(cards)
        amount = float(np.round(rng.lognormal(mean=4.8, sigma=1.0), 2))
        timestamp = start + timedelta(minutes=int(rng.integers(0, 60 * 24 * 60)))
        hour = timestamp.hour
        channel = random.choice(channels)
        country = random.choice(countries)

        risk = 0.02
        risk += 0.24 if user in risky_users else 0.0
        risk += 0.20 if device in risky_devices else 0.0
        risk += 0.18 if ip in risky_ips else 0.0
        risk += 0.20 if merchant in risky_merchants else 0.0
        risk += 0.13 if amount > 800 else 0.0
        risk += 0.08 if hour < 5 else 0.0
        risk += 0.05 if country in {"NG", "RU", "BR"} else 0.0
        risk += 0.06 if channel == "web" else 0.0
        risk += float(rng.normal(0, 0.04))
        risk = min(max(risk, 0.01), 0.98)
        is_fraud = int(rng.random() < risk)

        rows.append(
            {
                "transaction_id": f"T{i+1:06d}",
                "user_id": user,
                "device_id": device,
                "card_id": card,
                "ip_address": ip,
                "merchant_id": merchant,
                "amount": amount,
                "timestamp": timestamp.isoformat(),
                "channel": channel,
                "country": country,
                "is_fraud": is_fraud,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=2500)
    parser.add_argument("--out", type=str, default="data/transactions.csv")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_synthetic_transactions(args.rows)
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}")
    print(df.head().to_string(index=False))
    print("Fraud rate:", round(float(df["is_fraud"].mean()), 4))


if __name__ == "__main__":
    main()
