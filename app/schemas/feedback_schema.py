from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    transaction_id: str = Field(..., example="TNEW004")
    analyst_label: str = Field(..., example="fraud", description="fraud, not_fraud, or unknown")
    analyst_notes: Optional[str] = Field(default="", example="Confirmed suspicious shared device pattern.")
    reviewed_by: Optional[str] = Field(default="analyst", example="analyst_1")
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RetrainRequest(BaseModel):
    epochs: int = Field(default=5, ge=1, le=500)
    min_feedback: int = Field(default=1, ge=0)
    force: bool = Field(default=False)
