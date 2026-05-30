from typing import Any, Dict, List
from pydantic import BaseModel, Field


class TransactionRequest(BaseModel):
    transaction_id: str = Field(..., example="TNEW001")
    user_id: str = Field(..., example="U0001")
    device_id: str = Field(..., example="D0001")
    card_id: str = Field(..., example="C0001")
    ip_address: str = Field(..., example="IP0001")
    merchant_id: str = Field(..., example="M0001")
    amount: float = Field(..., example=1200)
    timestamp: str = Field(..., example="2026-05-29T03:00:01.189Z")
    channel: str = Field(..., example="web")
    country: str = Field(..., example="US")


class ScoreResponse(BaseModel):
    transaction_id: str

    gnn_graph_score: float
    ml_score: float
    final_risk: float
    decision: str
    reason_codes: List[str]

    neo4j_enabled: bool
    neo4j_graph_context: Dict[str, Any]

    model_versions: Dict[str, Any]

    data_quality: Dict[str, Any]
    agent_trace: Dict[str, Any]

    llm_explanation: Dict[str, Any] = Field(default_factory=dict)
