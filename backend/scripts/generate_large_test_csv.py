import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1000)
    parser.add_argument("--out", type=str, default="large_test_transactions.csv")
    args = parser.parse_args()

    random.seed(42)

    channels = ["web", "mobile", "pos"]
    countries = ["US", "IN", "GB", "CA", "NG", "BR", "RU"]
    base_time = datetime(2026, 5, 29, 3, 0, 1)

    rows = []

    for i in range(1, args.rows + 1):
        amount = round(random.choice([
            random.uniform(10, 500),
            random.uniform(500, 3000),
            random.uniform(3000, 15000),
        ]), 2)

        rows.append(
            {
                "transaction_id": f"TBULK{i:06d}",
                "user_id": f"U{random.randint(1, 400):04d}",
                "device_id": f"D{random.randint(1, 250):04d}",
                "card_id": f"C{random.randint(1, 350):04d}",
                "ip_address": f"IP{random.randint(1, 300):04d}",
                "merchant_id": f"M{random.randint(1, 100):04d}",
                "amount": amount,
                "timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
                "channel": random.choice(channels),
                "country": random.choice(countries),
            }
        )

    out_path = Path(args.out)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"Created {out_path} with {args.rows} rows.")


if __name__ == "__main__":
    main()
