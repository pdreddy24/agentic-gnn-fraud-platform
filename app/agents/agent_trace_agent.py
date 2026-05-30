from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AgentTraceAgent:
    """
    Agent Trace Agent

    Purpose:
    - Records which agents ran
    - Records status of each agent
    - Records details from each step
    - Returns trace in the /score API response
    """

    def __init__(self):
        self.current_trace: Dict[str, Any] = {}

    def start_trace(self, transaction_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new trace for one transaction scoring request.
        """

        self.current_trace = {
            "transaction_id": transaction_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": None,
            "agents_used": [],
            "steps": [],
            "status": "running",
        }

        return self.current_trace

    def add_step(
        self,
        agent_name: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add one agent execution step to the trace.
        """

        if not self.current_trace:
            self.start_trace()

        if agent_name not in self.current_trace["agents_used"]:
            self.current_trace["agents_used"].append(agent_name)

        self.current_trace["steps"].append(
            {
                "agent_name": agent_name,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": details or {},
            }
        )

    def finish_trace(self) -> Dict[str, Any]:
        """
        Finish and return the trace.
        """

        if not self.current_trace:
            self.start_trace()

        self.current_trace["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.current_trace["status"] = "completed"

        return self.current_trace

    def fail_trace(self, error: str) -> Dict[str, Any]:
        """
        Mark trace as failed.
        """

        if not self.current_trace:
            self.start_trace()

        self.current_trace["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.current_trace["status"] = "failed"
        self.current_trace["error"] = error

        return self.current_trace