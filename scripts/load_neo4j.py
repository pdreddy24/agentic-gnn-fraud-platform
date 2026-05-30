from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.services.neo4j_service import Neo4jService  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Load transaction graph data into Neo4j")
    parser.add_argument("--csv", default="data/transactions.csv", help="Path to transactions CSV")
    parser.add_argument("--clear", action="store_true", help="Delete all Neo4j nodes before loading")
    parser.add_argument("--limit", type=int, default=None, help="Optional row limit for fast testing")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    csv_path = ROOT / args.csv
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing {csv_path}. Run: python ml/generate_data.py --rows 2500")

    df = pd.read_csv(csv_path)
    if args.limit:
        df = df.head(args.limit)

    with Neo4jService() as neo4j:
        neo4j.verify()
        neo4j.setup_constraints()
        if args.clear:
            print("Clearing Neo4j database...")
            neo4j.clear_database()
            neo4j.setup_constraints()

        for i, row in enumerate(df.to_dict(orient="records"), start=1):
            neo4j.upsert_transaction_graph(row, is_fraud=row.get("is_fraud"))
            if i % 500 == 0:
                print(f"Loaded {i} rows...")

    print(f"Done. Loaded {len(df)} transactions into Neo4j.")
    print("Open Neo4j browser: http://localhost:7474")


if __name__ == "__main__":
    main()
