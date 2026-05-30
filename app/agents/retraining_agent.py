import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class RetrainingAgent:
    """
    Retraining Agent

    Purpose:
    - Checks whether enough feedback exists.
    - Runs ml/train_all.py to retrain GNN + tabular model.
    - Stores retraining run metadata in audits/retraining_runs.jsonl.

    Notes:
    - This is production-style orchestration, but still local.
    - For real production, this should run as a background job or CI/CD job.
    """

    def __init__(self, audit_dir: str = "audits"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_file = self.audit_dir / "feedback.jsonl"
        self.runs_file = self.audit_dir / "retraining_runs.jsonl"

    def run_retraining(
        self,
        epochs: int = 5,
        min_feedback: int = 1,
        force: bool = False,
    ) -> Dict[str, Any]:
        feedback_count = self._count_feedback()

        if feedback_count < min_feedback and not force:
            result = {
                "started": False,
                "reason": "not_enough_feedback",
                "feedback_count": feedback_count,
                "min_feedback": min_feedback,
                "hint": "Use force=true to retrain anyway.",
            }
            self._save_run(result)
            return result

        command = [
            sys.executable,
            "ml/train_all.py",
            "--epochs",
            str(epochs),
        ]

        started_at = datetime.now(timezone.utc).isoformat()

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60 * 20,
            )

            result = {
                "started": True,
                "success": completed.returncode == 0,
                "command": command,
                "feedback_count": feedback_count,
                "epochs": epochs,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "stdout": completed.stdout[-5000:],
                "stderr": completed.stderr[-5000:],
                "return_code": completed.returncode,
            }

            self._save_run(result)
            return result

        except Exception as exc:
            result = {
                "started": True,
                "success": False,
                "command": command,
                "feedback_count": feedback_count,
                "epochs": epochs,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }
            self._save_run(result)
            return result

    def list_runs(self, limit: int = 10) -> Dict[str, Any]:
        if not self.runs_file.exists():
            return {
                "count": 0,
                "records": [],
            }

        records = []
        with self.runs_file.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue

        return {
            "count": len(records),
            "records": records[-limit:],
        }

    def _count_feedback(self) -> int:
        if not self.feedback_file.exists():
            return 0

        count = 0
        with self.feedback_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    count += 1

        return count

    def _save_run(self, result: Dict[str, Any]) -> None:
        record = {
            "run_logged_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }

        with self.runs_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
