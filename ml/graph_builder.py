from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

NODE_TYPES = ["transaction", "user", "device", "card", "ip", "merchant"]
CHANNELS = ["web", "mobile", "pos"]
COUNTRIES = ["US", "IN", "GB", "CA", "NG", "BR", "RU"]
FEATURE_DIM = 23


@dataclass
class GraphData:
    node_ids: List[str]
    node_types: List[str]
    node_to_idx: Dict[str, int]
    x: torch.Tensor
    edge_index: torch.Tensor
    labels: torch.Tensor
    transaction_indices: torch.Tensor
    entity_stats: Dict[str, Dict[str, float]]


def _type_one_hot(node_type: str) -> List[float]:
    return [1.0 if node_type == t else 0.0 for t in NODE_TYPES]


def _safe_log_amount(amount: float) -> float:
    return float(np.log1p(max(float(amount), 0.0)) / 10.0)


def _transaction_features(row: pd.Series) -> List[float]:
    ts = pd.to_datetime(row["timestamp"])
    amount = float(row["amount"])
    channel = str(row.get("channel", "web"))
    country = str(row.get("country", "US"))
    features = []
    features.extend(_type_one_hot("transaction"))
    features.append(_safe_log_amount(amount))
    features.append(1.0 if amount > 800 else 0.0)
    features.append(ts.hour / 23.0)
    features.append(1.0 if ts.hour < 5 else 0.0)
    features.extend([1.0 if channel == c else 0.0 for c in CHANNELS])
    features.extend([1.0 if country == c else 0.0 for c in COUNTRIES])
    # Entity aggregate slots are zero for transaction nodes here.
    features.extend([0.0, 0.0, 0.0])
    return features[:FEATURE_DIM]


def _entity_features(entity_type: str, count: float, fraud_rate: float, avg_amount: float) -> List[float]:
    features = []
    features.extend(_type_one_hot(entity_type))
    features.extend([0.0] * 14)  # transaction-specific slots
    features.append(min(count / 100.0, 1.0))
    features.append(float(fraud_rate))
    features.append(_safe_log_amount(avg_amount))
    return features[:FEATURE_DIM]


def build_graph(df: pd.DataFrame) -> GraphData:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    entity_columns = {
        "user": "user_id",
        "device": "device_id",
        "card": "card_id",
        "ip": "ip_address",
        "merchant": "merchant_id",
    }

    node_ids: List[str] = []
    node_types: List[str] = []
    node_to_idx: Dict[str, int] = {}

    def add_node(node_id: str, node_type: str) -> int:
        if node_id not in node_to_idx:
            node_to_idx[node_id] = len(node_ids)
            node_ids.append(node_id)
            node_types.append(node_type)
        return node_to_idx[node_id]

    for _, row in df.iterrows():
        add_node(f"txn:{row.transaction_id}", "transaction")
        for entity_type, col in entity_columns.items():
            add_node(f"{entity_type}:{row[col]}", entity_type)

    # Build stats for entity nodes.
    entity_stats: Dict[str, Dict[str, float]] = {}
    for entity_type, col in entity_columns.items():
        stats = df.groupby(col).agg(count=("transaction_id", "count"), fraud_rate=("is_fraud", "mean"), avg_amount=("amount", "mean"))
        for key, row in stats.iterrows():
            entity_stats[f"{entity_type}:{key}"] = {
                "count": float(row["count"]),
                "fraud_rate": float(row["fraud_rate"]),
                "avg_amount": float(row["avg_amount"]),
            }

    x = np.zeros((len(node_ids), FEATURE_DIM), dtype=np.float32)
    labels = np.full(len(node_ids), -1, dtype=np.float32)
    transaction_indices: List[int] = []

    for _, row in df.iterrows():
        idx = node_to_idx[f"txn:{row.transaction_id}"]
        x[idx] = np.array(_transaction_features(row), dtype=np.float32)
        labels[idx] = float(row["is_fraud"])
        transaction_indices.append(idx)

    for node_id, idx in node_to_idx.items():
        if node_id.startswith("txn:"):
            continue
        node_type = node_id.split(":", 1)[0]
        stats = entity_stats.get(node_id, {"count": 0.0, "fraud_rate": 0.0, "avg_amount": 0.0})
        x[idx] = np.array(_entity_features(node_type, stats["count"], stats["fraud_rate"], stats["avg_amount"]), dtype=np.float32)

    edges: List[Tuple[int, int]] = []
    for _, row in df.iterrows():
        txn_idx = node_to_idx[f"txn:{row.transaction_id}"]
        for entity_type, col in entity_columns.items():
            ent_idx = node_to_idx[f"{entity_type}:{row[col]}"]
            edges.append((txn_idx, ent_idx))
            edges.append((ent_idx, txn_idx))

    edge_index = torch.tensor(edges, dtype=torch.long).T.contiguous()
    return GraphData(
        node_ids=node_ids,
        node_types=node_types,
        node_to_idx=node_to_idx,
        x=torch.tensor(x, dtype=torch.float32),
        edge_index=edge_index,
        labels=torch.tensor(labels, dtype=torch.float32),
        transaction_indices=torch.tensor(transaction_indices, dtype=torch.long),
        entity_stats=entity_stats,
    )


def build_new_transaction_node_features(transaction: dict) -> np.ndarray:
    row = pd.Series(transaction)
    if "timestamp" not in row or pd.isna(row["timestamp"]):
        row["timestamp"] = pd.Timestamp.utcnow().isoformat()
    if "channel" not in row:
        row["channel"] = "web"
    if "country" not in row:
        row["country"] = "US"
    return np.array(_transaction_features(row), dtype=np.float32)


def build_entity_feature_for_inference(node_id: str, entity_stats: Dict[str, Dict[str, float]]) -> np.ndarray:
    node_type = node_id.split(":", 1)[0]
    stats = entity_stats.get(node_id, {"count": 0.0, "fraud_rate": 0.0, "avg_amount": 0.0})
    return np.array(_entity_features(node_type, stats["count"], stats["fraud_rate"], stats["avg_amount"]), dtype=np.float32)
