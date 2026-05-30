from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import torch

import sys

# Allow importing training-time graph/model utilities
ML_DIR = Path(__file__).resolve().parents[2] / "ml"
if str(ML_DIR) not in sys.path:
    sys.path.append(str(ML_DIR))

from graph_builder import (  # noqa: E402
    FEATURE_DIM,
    build_entity_feature_for_inference,
    build_new_transaction_node_features,
)
from train_all import SimpleGraphSAGE  # noqa: E402


class GNNGraphAgent:
    """
    GNN Graph Agent

    Purpose:
    - Loads trained GraphSAGE model
    - Loads graph_artifact.joblib
    - Attaches a new transaction node to the existing graph
    - Runs GNN inference
    - Returns fraud graph score
    """

    def __init__(self, artifact_dir: str = "artifacts"):
        artifact_dir_path = Path(artifact_dir)

        self.model_path = artifact_dir_path / "gnn_model.pt"
        self.graph_path = artifact_dir_path / "graph_artifact.joblib"

        self.model = None
        self.graph_payload = None
        self.version = "simple_graphsage_v1"

        if not self.model_path.exists():
            print(f"GNNGraphAgent warning: missing {self.model_path}")
            return

        if not self.graph_path.exists():
            print(f"GNNGraphAgent warning: missing {self.graph_path}")
            return

        self.graph_payload = joblib.load(self.graph_path)

        self.model = SimpleGraphSAGE(in_dim=FEATURE_DIM, hidden_dim=64)

        try:
            state_dict = torch.load(
                self.model_path,
                map_location="cpu",
                weights_only=True,
            )
        except TypeError:
            state_dict = torch.load(self.model_path, map_location="cpu")

        self.model.load_state_dict(state_dict)
        self.model.eval()

    def predict(self, transaction: Dict[str, Any]) -> float:
        """
        Return GNN fraud probability for the transaction.
        """

        if self.model is None or self.graph_payload is None:
            return 0.0

        try:
            result = self.score(transaction)
            return round(float(result.get("score", 0.0)), 4)
        except Exception as exc:
            print(f"GNNGraphAgent prediction failed: {exc}")
            return 0.0

    def score(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full GNN scoring output.
        """

        x, edge_index, new_tx_idx, entity_nodes = self._build_inference_graph(transaction)

        with torch.no_grad():
            logits = self.model(x, edge_index)
            score = torch.sigmoid(logits[new_tx_idx]).item()

        reason_codes = []
        stats = self.graph_payload.get("entity_stats", {})

        for node in entity_nodes:
            node_type = node.split(":")[0].upper()
            s = stats.get(node)

            if not s:
                reason_codes.append(f"NEW_{node_type}")
                continue

            if s.get("fraud_rate", 0.0) > 0.35:
                reason_codes.append(f"HIGH_{node_type}_FRAUD_RATE")

            if s.get("count", 0.0) > 25 and node.startswith(("device:", "ip:")):
                reason_codes.append(f"SHARED_{node_type}_MANY_TRANSACTIONS")

        return {
            "score": float(score),
            "reason_codes": sorted(set(reason_codes)),
        }

    def _build_inference_graph(
        self,
        transaction: Dict[str, Any],
    ) -> Tuple[torch.Tensor, torch.Tensor, int, List[str]]:
        """
        Build inference graph by adding new transaction node and its related entity nodes.
        """

        base_x = np.array(self.graph_payload["x"], dtype=np.float32)
        base_edges = np.array(self.graph_payload["edge_index"], dtype=np.int64)

        node_to_idx = dict(self.graph_payload["node_to_idx"])
        node_ids = list(self.graph_payload["node_ids"])
        entity_stats = self.graph_payload.get("entity_stats", {})

        new_tx_node = f"txn:{transaction['transaction_id']}"
        new_tx_idx = len(node_ids)
        node_ids.append(new_tx_node)

        x_rows = [
            base_x,
            build_new_transaction_node_features(transaction).reshape(1, -1),
        ]

        entity_nodes = [
            f"user:{transaction['user_id']}",
            f"device:{transaction['device_id']}",
            f"card:{transaction['card_id']}",
            f"ip:{transaction['ip_address']}",
            f"merchant:{transaction['merchant_id']}",
        ]

        extra_edges: List[Tuple[int, int]] = []

        current_size = new_tx_idx + 1

        for ent_node in entity_nodes:
            if ent_node in node_to_idx:
                ent_idx = node_to_idx[ent_node]
            else:
                ent_idx = current_size
                current_size += 1
                node_ids.append(ent_node)

                ent_features = build_entity_feature_for_inference(
                    ent_node,
                    entity_stats,
                ).reshape(1, -1)

                x_rows.append(ent_features)

            extra_edges.append((new_tx_idx, ent_idx))
            extra_edges.append((ent_idx, new_tx_idx))

        x = torch.tensor(np.vstack(x_rows), dtype=torch.float32)

        new_edges = np.array(extra_edges, dtype=np.int64).T
        edge_index = torch.tensor(
            np.hstack([base_edges, new_edges]),
            dtype=torch.long,
        )

        return x, edge_index, new_tx_idx, entity_nodes