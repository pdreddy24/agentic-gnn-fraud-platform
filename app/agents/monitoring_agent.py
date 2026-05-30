import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List


class MonitoringAgent:
    """
    Monitoring Agent

    Purpose:
    - Reads scoring audit logs and feedback logs.
    - Computes basic production monitoring metrics.
    - Tracks decision counts, score averages, model versions, and failed agent steps.
    """

    def __init__(self, audit_dir: str = "audits"):
        self.audit_dir = Path(audit_dir)
        self.audit_file = self.audit_dir / "scoring_audit.jsonl"
        self.feedback_file = self.audit_dir / "feedback.jsonl"

    def get_summary(self, recent_limit: int = 100) -> Dict[str, Any]:
        audits = self._read_jsonl(self.audit_file)
        feedback = self._read_jsonl(self.feedback_file)

        if not audits:
            return {
                "status": "no_audits_yet",
                "total_scored_transactions": 0,
                "message": "Run POST /score first.",
            }

        recent = audits[-recent_limit:]

        decisions = Counter(str(r.get("decision", "UNKNOWN")) for r in recent)
        reason_codes = Counter()
        model_versions = Counter()
        agent_failures = Counter()

        final_risks = []
        gnn_scores = []
        ml_scores = []
        neo4j_risks = []

        for record in recent:
            final_risks.append(float(record.get("final_risk", 0.0) or 0.0))
            gnn_scores.append(float(record.get("gnn_graph_score", 0.0) or 0.0))
            ml_scores.append(float(record.get("ml_score", 0.0) or 0.0))

            neo4j_context = record.get("neo4j_graph_context", {}) or {}
            neo4j_risks.append(float(neo4j_context.get("neo4j_graph_risk", 0.0) or 0.0))

            for code in record.get("reason_codes", []) or []:
                reason_codes[str(code)] += 1

            versions = record.get("model_versions", {}) or {}
            for name, version in versions.items():
                model_versions[f"{name}:{version}"] += 1

            trace = record.get("agent_trace", {}) or {}
            for step in trace.get("steps", []) or []:
                if step.get("status") != "completed":
                    agent_failures[step.get("agent_name", "UNKNOWN")] += 1

        feedback_labels = Counter(str(r.get("analyst_label", "unknown")) for r in feedback)

        return {
            "status": "ok",
            "total_scored_transactions": len(audits),
            "recent_window_size": len(recent),
            "decision_counts": dict(decisions),
            "average_scores": {
                "final_risk": round(mean(final_risks), 4) if final_risks else 0.0,
                "gnn_graph_score": round(mean(gnn_scores), 4) if gnn_scores else 0.0,
                "ml_score": round(mean(ml_scores), 4) if ml_scores else 0.0,
                "neo4j_graph_risk": round(mean(neo4j_risks), 4) if neo4j_risks else 0.0,
            },
            "top_reason_codes": dict(reason_codes.most_common(10)),
            "model_versions_seen": dict(model_versions),
            "agent_failures": dict(agent_failures),
            "feedback_count": len(feedback),
            "feedback_labels": dict(feedback_labels),
            "latest_transaction": recent[-1] if recent else None,
        }

    def get_drift_report(self, baseline_size: int = 100, recent_size: int = 25) -> Dict[str, Any]:
        audits = self._read_jsonl(self.audit_file)

        if len(audits) < max(10, recent_size):
            return {
                "status": "not_enough_data",
                "message": "Need more scored transactions for drift comparison.",
                "total_scored_transactions": len(audits),
            }

        baseline = audits[:baseline_size] if len(audits) >= baseline_size else audits
        recent = audits[-recent_size:]

        def avg(records: List[Dict[str, Any]], key: str) -> float:
            vals = [float(r.get(key, 0.0) or 0.0) for r in records]
            return mean(vals) if vals else 0.0

        baseline_final = avg(baseline, "final_risk")
        recent_final = avg(recent, "final_risk")

        drift_amount = abs(recent_final - baseline_final)

        if drift_amount >= 0.20:
            drift_status = "high_drift"
        elif drift_amount >= 0.10:
            drift_status = "medium_drift"
        else:
            drift_status = "low_drift"

        return {
            "status": drift_status,
            "baseline_size": len(baseline),
            "recent_size": len(recent),
            "baseline_average_final_risk": round(baseline_final, 4),
            "recent_average_final_risk": round(recent_final, 4),
            "absolute_difference": round(drift_amount, 4),
        }

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []

        records: List[Dict[str, Any]] = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

        return records
