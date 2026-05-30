import os
from typing import Any, Dict

from neo4j import GraphDatabase
from dotenv import load_dotenv


load_dotenv()


class Neo4jGraphAgent:
    """
    Neo4j Graph Agent

    Purpose:
    - Connects to Neo4j
    - Reads graph context for a transaction
    - Finds shared device/card/IP usage
    - Finds merchant fraud rate
    - Returns graph context to the orchestrator
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_NEO4J", "false").lower() == "true"

        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password123")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        self.driver = None

        if self.enabled:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password)
                )

                # Test connection
                with self.driver.session(database=self.database) as session:
                    session.run("RETURN 1 AS ok").single()

                print("Neo4jGraphAgent connected successfully.")

            except Exception as exc:
                print(f"Neo4jGraphAgent connection failed: {exc}")
                self.enabled = False
                self.driver = None

    def get_graph_context(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch graph context from Neo4j for the incoming transaction.
        """

        if not self.enabled or self.driver is None:
            return {
                "enabled": False,
                "message": "Neo4j is disabled or not connected",
                "device_user_count": 0,
                "ip_user_count": 0,
                "card_user_count": 0,
                "merchant_transaction_count": 0,
                "merchant_fraud_count": 0,
                "merchant_fraud_rate": 0.0,
                "shared_device_risk": 0.0,
                "shared_ip_risk": 0.0,
                "shared_card_risk": 0.0,
                "neo4j_graph_risk": 0.0,
            }

        user_id = transaction.get("user_id")
        device_id = transaction.get("device_id")
        card_id = transaction.get("card_id")
        ip_address = transaction.get("ip_address")
        merchant_id = transaction.get("merchant_id")

        query = """
        OPTIONAL MATCH (d:Device {device_id: $device_id})<-[:USED_DEVICE]-(du:User)
        WITH count(DISTINCT du) AS device_user_count

        OPTIONAL MATCH (ip:IP {ip_address: $ip_address})<-[:USED_IP]-(iu:User)
        WITH device_user_count, count(DISTINCT iu) AS ip_user_count

        OPTIONAL MATCH (c:Card {card_id: $card_id})<-[:USED_CARD]-(cu:User)
        WITH device_user_count, ip_user_count, count(DISTINCT cu) AS card_user_count

        OPTIONAL MATCH (m:Merchant {merchant_id: $merchant_id})<-[:PAID_TO]-(t:Transaction)
        WITH
            device_user_count,
            ip_user_count,
            card_user_count,
            count(t) AS merchant_transaction_count,
            sum(CASE WHEN coalesce(t.is_fraud, 0) = 1 THEN 1 ELSE 0 END) AS merchant_fraud_count

        RETURN
            device_user_count,
            ip_user_count,
            card_user_count,
            merchant_transaction_count,
            merchant_fraud_count
        """

        try:
            with self.driver.session(database=self.database) as session:
                record = session.run(
                    query,
                    device_id=device_id,
                    ip_address=ip_address,
                    card_id=card_id,
                    merchant_id=merchant_id,
                    user_id=user_id,
                ).single()

            if record is None:
                return self._empty_context(enabled=True)

            device_user_count = int(record.get("device_user_count") or 0)
            ip_user_count = int(record.get("ip_user_count") or 0)
            card_user_count = int(record.get("card_user_count") or 0)
            merchant_transaction_count = int(record.get("merchant_transaction_count") or 0)
            merchant_fraud_count = int(record.get("merchant_fraud_count") or 0)

            if merchant_transaction_count > 0:
                merchant_fraud_rate = merchant_fraud_count / merchant_transaction_count
            else:
                merchant_fraud_rate = 0.0

            shared_device_risk = self._count_to_risk(device_user_count, normal_limit=1, high_limit=5)
            shared_ip_risk = self._count_to_risk(ip_user_count, normal_limit=2, high_limit=8)
            shared_card_risk = self._count_to_risk(card_user_count, normal_limit=1, high_limit=4)

            neo4j_graph_risk = (
                0.30 * shared_device_risk
                + 0.25 * shared_ip_risk
                + 0.25 * shared_card_risk
                + 0.20 * merchant_fraud_rate
            )

            neo4j_graph_risk = max(0.0, min(1.0, neo4j_graph_risk))

            return {
                "enabled": True,
                "device_user_count": device_user_count,
                "ip_user_count": ip_user_count,
                "card_user_count": card_user_count,
                "merchant_transaction_count": merchant_transaction_count,
                "merchant_fraud_count": merchant_fraud_count,
                "merchant_fraud_rate": round(float(merchant_fraud_rate), 4),
                "shared_device_risk": round(float(shared_device_risk), 4),
                "shared_ip_risk": round(float(shared_ip_risk), 4),
                "shared_card_risk": round(float(shared_card_risk), 4),
                "neo4j_graph_risk": round(float(neo4j_graph_risk), 4),
            }

        except Exception as exc:
            return {
                "enabled": False,
                "error": str(exc),
                "device_user_count": 0,
                "ip_user_count": 0,
                "card_user_count": 0,
                "merchant_transaction_count": 0,
                "merchant_fraud_count": 0,
                "merchant_fraud_rate": 0.0,
                "shared_device_risk": 0.0,
                "shared_ip_risk": 0.0,
                "shared_card_risk": 0.0,
                "neo4j_graph_risk": 0.0,
            }

    def save_scored_transaction(
        self,
        transaction: Dict[str, Any],
        final_risk: float,
        decision: str,
        gnn_graph_score: float,
        ml_score: float,
    ) -> bool:
        """
        Optional production-style method.

        Saves newly scored transaction back into Neo4j.
        This lets the graph grow over time.
        """

        if not self.enabled or self.driver is None:
            return False

        query = """
        MERGE (u:User {user_id: $user_id})
        MERGE (d:Device {device_id: $device_id})
        MERGE (c:Card {card_id: $card_id})
        MERGE (ip:IP {ip_address: $ip_address})
        MERGE (m:Merchant {merchant_id: $merchant_id})

        MERGE (t:Transaction {transaction_id: $transaction_id})
        SET
            t.amount = $amount,
            t.timestamp = $timestamp,
            t.channel = $channel,
            t.country = $country,
            t.final_risk = $final_risk,
            t.decision = $decision,
            t.gnn_graph_score = $gnn_graph_score,
            t.ml_score = $ml_score

        MERGE (u)-[:MADE]->(t)
        MERGE (u)-[:USED_DEVICE]->(d)
        MERGE (u)-[:USED_CARD]->(c)
        MERGE (u)-[:USED_IP]->(ip)
        MERGE (t)-[:PAID_TO]->(m)
        """

        try:
            with self.driver.session(database=self.database) as session:
                session.run(
                    query,
                    transaction_id=transaction.get("transaction_id"),
                    user_id=transaction.get("user_id"),
                    device_id=transaction.get("device_id"),
                    card_id=transaction.get("card_id"),
                    ip_address=transaction.get("ip_address"),
                    merchant_id=transaction.get("merchant_id"),
                    amount=float(transaction.get("amount", 0.0)),
                    timestamp=str(transaction.get("timestamp")),
                    channel=transaction.get("channel"),
                    country=transaction.get("country"),
                    final_risk=float(final_risk),
                    decision=decision,
                    gnn_graph_score=float(gnn_graph_score),
                    ml_score=float(ml_score),
                )
            return True

        except Exception as exc:
            print(f"Failed to save scored transaction to Neo4j: {exc}")
            return False

    def _count_to_risk(self, count: int, normal_limit: int, high_limit: int) -> float:
        """
        Converts relationship counts into risk score between 0 and 1.
        """

        if count <= normal_limit:
            return 0.0

        if count >= high_limit:
            return 1.0

        return (count - normal_limit) / (high_limit - normal_limit)

    def _empty_context(self, enabled: bool = True) -> Dict[str, Any]:
        return {
            "enabled": enabled,
            "device_user_count": 0,
            "ip_user_count": 0,
            "card_user_count": 0,
            "merchant_transaction_count": 0,
            "merchant_fraud_count": 0,
            "merchant_fraud_rate": 0.0,
            "shared_device_risk": 0.0,
            "shared_ip_risk": 0.0,
            "shared_card_risk": 0.0,
            "neo4j_graph_risk": 0.0,
        }

    def close(self):
        """
        Close Neo4j database connection.
        """

        if self.driver is not None:
            self.driver.close()
            self.driver = None