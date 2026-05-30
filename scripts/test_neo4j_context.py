from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.services.neo4j_service import Neo4jService  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env")
    tx = {
        "transaction_id": "TNEO4J_TEST",
        "user_id": "U0001",
        "device_id": "D0001",
        "card_id": "C0001",
        "ip_address": "IP0001",
        "merchant_id": "M0001",
        "amount": 1800.0,
        "timestamp": "2026-05-28T23:15:00",
        "channel": "web",
        "country": "US",
    }
    with Neo4jService() as neo4j:
        neo4j.verify()
        neo4j.setup_constraints()
        neo4j.upsert_transaction_graph(tx)
        print(neo4j.get_graph_context(tx))


if __name__ == "__main__":
    main()
