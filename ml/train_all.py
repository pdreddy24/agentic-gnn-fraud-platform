from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder

from graph_builder import FEATURE_DIM, build_graph


class MeanGraphSAGELayer(nn.Module):
    def __init__(self, in_dim: int, out_dim: int):
        super().__init__()
        self.self_linear = nn.Linear(in_dim, out_dim)
        self.neigh_linear = nn.Linear(in_dim, out_dim)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        src, dst = edge_index
        neigh_sum = torch.zeros_like(x)
        neigh_sum.index_add_(0, dst, x[src])
        deg = torch.zeros(x.size(0), device=x.device)
        deg.index_add_(0, dst, torch.ones_like(dst, dtype=torch.float32))
        neigh_mean = neigh_sum / deg.clamp(min=1).unsqueeze(1)
        return self.self_linear(x) + self.neigh_linear(neigh_mean)


class SimpleGraphSAGE(nn.Module):
    def __init__(self, in_dim: int = FEATURE_DIM, hidden_dim: int = 64):
        super().__init__()
        self.layer1 = MeanGraphSAGELayer(in_dim, hidden_dim)
        self.layer2 = MeanGraphSAGELayer(hidden_dim, hidden_dim)
        self.classifier = nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.layer1(x, edge_index))
        h = F.dropout(h, p=0.20, training=self.training)
        h = F.relu(self.layer2(h, edge_index))
        return self.classifier(h).squeeze(-1)


def tabular_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["timestamp"].dt.hour
    df["is_night"] = (df["hour"] < 5).astype(int)
    df["log_amount"] = np.log1p(df["amount"])
    for col in ["user_id", "device_id", "card_id", "ip_address", "merchant_id"]:
        counts = df[col].map(df[col].value_counts())
        df[f"{col}_count"] = counts.astype(float)
    return df[["amount", "log_amount", "hour", "is_night", "channel", "country", "user_id_count", "device_id_count", "card_id_count", "ip_address_count", "merchant_id_count"]]


def train_tabular(df: pd.DataFrame, artifact_dir: Path) -> dict:
    X_raw = tabular_features(df)
    y = df["is_fraud"].astype(int).values
    cat_cols = ["channel", "country"]
    num_cols = [c for c in X_raw.columns if c not in cat_cols]

    encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    X_cat = encoder.fit_transform(X_raw[cat_cols])
    X_num = X_raw[num_cols].to_numpy(dtype=np.float32)
    X = np.hstack([X_num, X_cat])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=180, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    metrics = {
        "tabular_roc_auc": float(roc_auc_score(y_test, proba)),
        "tabular_avg_precision": float(average_precision_score(y_test, proba)),
    }
    joblib.dump({"model": model, "encoder": encoder, "num_cols": num_cols, "cat_cols": cat_cols}, artifact_dir / "tabular_model.joblib")
    return metrics


def train_gnn(df: pd.DataFrame, artifact_dir: Path, epochs: int = 80) -> dict:
    graph = build_graph(df)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleGraphSAGE().to(device)
    x = graph.x.to(device)
    edge_index = graph.edge_index.to(device)
    labels = graph.labels.to(device)
    tx_idx = graph.transaction_indices.to(device)

    tx_labels = labels[tx_idx]
    idx_np = tx_idx.cpu().numpy()
    label_np = tx_labels.cpu().numpy()
    train_idx_np, test_idx_np = train_test_split(idx_np, test_size=0.25, random_state=42, stratify=label_np)
    train_idx = torch.tensor(train_idx_np, dtype=torch.long, device=device)
    test_idx = torch.tensor(test_idx_np, dtype=torch.long, device=device)

    fraud_rate = float(label_np.mean())
    pos_weight = torch.tensor([(1.0 - fraud_rate) / max(fraud_rate, 1e-4)], dtype=torch.float32, device=device)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.005, weight_decay=1e-4)

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(x, edge_index)
        loss = loss_fn(logits[train_idx], labels[train_idx])
        loss.backward()
        optimizer.step()
        if epoch % 20 == 0:
            print(f"GNN epoch {epoch:03d} | loss={loss.item():.4f}")

    model.eval()
    with torch.no_grad():
        logits = model(x, edge_index)
        proba = torch.sigmoid(logits[test_idx]).cpu().numpy()
        y_true = labels[test_idx].cpu().numpy()
    metrics = {
        "gnn_roc_auc": float(roc_auc_score(y_true, proba)),
        "gnn_avg_precision": float(average_precision_score(y_true, proba)),
    }

    torch.save(model.state_dict(), artifact_dir / "gnn_model.pt")
    graph_payload = {
        "node_ids": graph.node_ids,
        "node_types": graph.node_types,
        "node_to_idx": graph.node_to_idx,
        "x": graph.x.numpy(),
        "edge_index": graph.edge_index.numpy(),
        "entity_stats": graph.entity_stats,
    }
    joblib.dump(graph_payload, artifact_dir / "graph_artifact.joblib")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/transactions.csv")
    parser.add_argument("--artifacts", default="artifacts")
    parser.add_argument("--epochs", type=int, default=80)
    args = parser.parse_args()

    data_path = Path(args.data)
    artifact_dir = Path(args.artifacts)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"{data_path} not found. Run: python ml/generate_data.py")

    df = pd.read_csv(data_path)
    print(f"Training on {len(df)} transactions. Fraud rate={df['is_fraud'].mean():.4f}")
    metrics = {}
    metrics.update(train_tabular(df, artifact_dir))
    metrics.update(train_gnn(df, artifact_dir, args.epochs))
    (artifact_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print("Training complete.")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
