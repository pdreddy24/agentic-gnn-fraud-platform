from __future__ import annotations

import os
from contextlib import AbstractContextManager
from typing import Any, Dict, Optional

from neo4j import GraphDatabase, Driver


class Neo4jService(AbstractContextManager):
    """Small Neo4j wrapper for the fraud graph.

    Neo4j stores the relationship graph. The GNN model is still trained/served
    separately using PyTorch artifacts. This service gives agents access to
    real graph context such as shared devices, shared IPs, and entity fraud rates.
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password123")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self) -> None:
        self.driver.close()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def verify(self) -> bool:
        self.driver.verify_connectivity()
        return True

    def setup_constraints(self) -> None:
        """Create unique constraints. Safe to run multiple times."""
        statements = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (n:User) REQUIRE n.user_id IS UNIQUE",
            "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (n:Device) REQUIRE n.device_id IS UNIQUE",
            "CREATE CONSTRAINT card_id_unique IF NOT EXISTS FOR (n:Card) REQUIRE n.card_id IS UNIQUE",
            "CREATE CONSTRAINT ip_id_unique IF NOT EXISTS FOR (n:IPAddress) REQUIRE n.ip_address IS UNIQUE",
            "CREATE CONSTRAINT merchant_id_unique IF NOT EXISTS FOR (n:Merchant) REQUIRE n.merchant_id IS UNIQUE",
            "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (n:Transaction) REQUIRE n.transaction_id IS UNIQUE",
        ]
        with self.driver.session(database=self.database) as session:
            for stmt in statements:
                session.run(stmt)

    def upsert_transaction_graph(self, tx: Dict[str, Any], is_fraud: Optional[int] = None) -> None:
        """Insert/update one transaction and its relationships."""
        params = {
            "transaction_id": str(tx["transaction_id"]),
            "user_id": str(tx["user_id"]),
            "device_id": str(tx["device_id"]),
            "card_id": str(tx["card_id"]),
            "ip_address": str(tx["ip_address"]),
            "merchant_id": str(tx["merchant_id"]),
            "amount": float(tx["amount"]),
            "timestamp": str(tx.get("timestamp") or ""),
            "channel": str(tx.get("channel", "unknown")),
            "country": str(tx.get("country", "unknown")),
            "is_fraud": None if is_fraud is None else int(is_fraud),
        }
        cypher = """
        MERGE (u:User {user_id: $user_id})
        MERGE (d:Device {device_id: $device_id})
        MERGE (c:Card {card_id: $card_id})
        MERGE (ip:IPAddress {ip_address: $ip_address})
        MERGE (m:Merchant {merchant_id: $merchant_id})
        MERGE (t:Transaction {transaction_id: $transaction_id})
        SET t.amount = $amount,
            t.timestamp = $timestamp,
            t.channel = $channel,
            t.country = $country,
            t.is_fraud = coalesce($is_fraud, t.is_fraud)
        MERGE (u)-[:MADE]->(t)
        MERGE (u)-[:USED_DEVICE]->(d)
        MERGE (u)-[:USED_CARD]->(c)
        MERGE (u)-[:USED_IP]->(ip)
        MERGE (t)-[:USED_CARD]->(c)
        MERGE (t)-[:FROM_IP]->(ip)
        MERGE (t)-[:FROM_DEVICE]->(d)
        MERGE (t)-[:PAID_TO]->(m)
        """
        with self.driver.session(database=self.database) as session:
            session.run(cypher, params)

    def get_graph_context(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Return graph features/reasons for a transaction from Neo4j."""
        params = {
            "user_id": str(tx["user_id"]),
            "device_id": str(tx["device_id"]),
            "card_id": str(tx["card_id"]),
            "ip_address": str(tx["ip_address"]),
            "merchant_id": str(tx["merchant_id"]),
        }
        cypher = """
        OPTIONAL MATCH (:User)-[:USED_DEVICE]->(d:Device {device_id: $device_id})
        WITH count(DISTINCT d) AS device_exists, count(DISTINCT CASE WHEN d IS NULL THEN null ELSE d END) AS _ignore
        OPTIONAL MATCH (du:User)-[:USED_DEVICE]->(:Device {device_id: $device_id})
        WITH count(DISTINCT du) AS shared_device_users
        OPTIONAL MATCH (iu:User)-[:USED_IP]->(:IPAddress {ip_address: $ip_address})
        WITH shared_device_users, count(DISTINCT iu) AS shared_ip_users
        OPTIONAL MATCH (cu:User)-[:USED_CARD]->(:Card {card_id: $card_id})
        WITH shared_device_users, shared_ip_users, count(DISTINCT cu) AS shared_card_users
        OPTIONAL MATCH (mt:Transaction)-[:PAID_TO]->(:Merchant {merchant_id: $merchant_id})
        WITH shared_device_users, shared_ip_users, shared_card_users,
             count(mt) AS merchant_tx_count,
             avg(CASE WHEN mt.is_fraud = 1 THEN 1.0 ELSE 0.0 END) AS merchant_fraud_rate
        OPTIONAL MATCH (dt:Transaction)-[:FROM_DEVICE]->(:Device {device_id: $device_id})
        WITH shared_device_users, shared_ip_users, shared_card_users, merchant_tx_count, merchant_fraud_rate,
             count(dt) AS device_tx_count,
             avg(CASE WHEN dt.is_fraud = 1 THEN 1.0 ELSE 0.0 END) AS device_fraud_rate
        OPTIONAL MATCH (it:Transaction)-[:FROM_IP]->(:IPAddress {ip_address: $ip_address})
        RETURN shared_device_users,
               shared_ip_users,
               shared_card_users,
               merchant_tx_count,
               coalesce(merchant_fraud_rate, 0.0) AS merchant_fraud_rate,
               device_tx_count,
               coalesce(device_fraud_rate, 0.0) AS device_fraud_rate,
               count(it) AS ip_tx_count,
               coalesce(avg(CASE WHEN it.is_fraud = 1 THEN 1.0 ELSE 0.0 END), 0.0) AS ip_fraud_rate
        """
        with self.driver.session(database=self.database) as session:
            record = session.run(cypher, params).single()
            if record is None:
                return {}
            return dict(record)

    def clear_database(self) -> None:
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
