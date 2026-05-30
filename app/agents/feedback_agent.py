import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class FeedbackAgent:
    """
    Feedback Agent

    Purpose:
    - Stores analyst feedback after a transaction is reviewed.
    - Creates a feedback loop for future retraining.
    - Saves records to audits/feedback.jsonl.

    Example:
    transaction_id = TNEW004
    analyst_label = fraud / not_fraud
    analyst_notes = "Confirmed suspicious shared device pattern"
    """

    VALID_LABELS = {"fraud", "not_fraud", "unknown"}

    def __init__(self, audit_dir: str = "audits"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.audit_dir / "feedback.jsonl"

    def save_feedback(
        self,
        transaction_id: str,
        analyst_label: str,
        analyst_notes: Optional[str] = None,
        reviewed_by: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        label = analyst_label.strip().lower()

        if label not in self.VALID_LABELS:
            return {
                "saved": False,
                "error": f"Invalid analyst_label '{analyst_label}'. Use one of {sorted(self.VALID_LABELS)}",
            }

        record = {
            "feedback_id": f"FB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "transaction_id": transaction_id,
            "analyst_label": label,
            "analyst_notes": analyst_notes or "",
            "reviewed_by": reviewed_by or "analyst",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "extra": extra or {},
        }

        with self.feedback_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")

        return {
            "saved": True,
            "feedback": record,
        }

    def list_feedback(self, limit: int = 20) -> Dict[str, Any]:
        if not self.feedback_file.exists():
            return {
                "count": 0,
                "records": [],
            }

        records: List[Dict[str, Any]] = []

        with self.feedback_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

        return {
            "count": len(records),
            "records": records[-limit:],
        }
