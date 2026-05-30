import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class AuditAgent:
    """
    Audit Agent

    Purpose:
    - Saves every /score response into audits/scoring_audit.jsonl
    - Creates audits folder automatically
    - Stores one JSON record per scored transaction
    """

    def __init__(self, audit_dir: str = "audits"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.audit_dir / "scoring_audit.jsonl"

    def save(self, response: Dict[str, Any]) -> bool:
        try:
            audit_record = {
                "audit_timestamp": datetime.now(timezone.utc).isoformat(),
                "transaction_id": response.get("transaction_id"),
                "decision": response.get("decision"),
                "final_risk": response.get("final_risk"),
                "gnn_graph_score": response.get("gnn_graph_score"),
                "ml_score": response.get("ml_score"),
                "reason_codes": response.get("reason_codes", []),
                "neo4j_enabled": response.get("neo4j_enabled"),
                "neo4j_graph_context": response.get("neo4j_graph_context", {}),
                "model_versions": response.get("model_versions", {}),
                "data_quality": response.get("data_quality", {}),
                "agent_trace": response.get("agent_trace", {}),
            }

            with self.audit_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(audit_record, default=str) + "\n")

            return True

        except Exception as exc:
            print(f"AuditAgent failed to save audit: {exc}")
            return False