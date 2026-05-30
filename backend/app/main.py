import csv
import io
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.database import (
    compare_batches,
    create_batch,
    create_session,
    create_user,
    get_predictions,
    get_user_by_token,
    init_db,
    list_batches,
    save_prediction,
    save_uploaded_file,
    verify_user,
)
from app.schemas.auth_schema import LoginRequest, SignupRequest
from app.schemas.transaction_schema import TransactionRequest, ScoreResponse
from app.schemas.feedback_schema import FeedbackRequest, RetrainRequest

from app.agents.triage_orchestrator_agent import TriageOrchestratorAgent
from app.agents.feedback_agent import FeedbackAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.retraining_agent import RetrainingAgent
from app.agents.fraud_explanation_agent import FraudExplanationAgent


app = FastAPI(
    title="Full-Stack Hybrid Fraud Detection Platform",
    description=(
        "Fraud detection platform with signup/login, CSV upload, stored prediction history, "
        "batch comparison, LangGraph agents, GNN, tabular ML, Neo4j, and LLM explanations."
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TriageOrchestratorAgent()
feedback_agent = FeedbackAgent()
monitoring_agent = MonitoringAgent()
retraining_agent = RetrainingAgent()
fraud_explanation_agent = FraudExplanationAgent()


@app.on_event("startup")
def startup():
    init_db()


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header.")

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header.")

    token = parts[1]
    user = get_user_by_token(token)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return user


def add_explanation_for_bulk(result: Dict[str, Any], use_llm_for_approved: bool = False) -> Dict[str, Any]:
    decision = result.get("decision", "UNKNOWN")

    if decision in ["REVIEW", "BLOCK"] or use_llm_for_approved:
        result["llm_explanation"] = fraud_explanation_agent.explain(result)
    else:
        result["llm_explanation"] = {
            "summary": "Low-risk transaction approved. Detailed LLM review was skipped for this approved transaction.",
            "risk_level": "LOW",
            "main_risk_factors": result.get("reason_codes", []),
            "recommended_actions": ["Approve transaction.", "Continue standard monitoring."],
            "analyst_note": "LLM explanation skipped for low-risk approved transaction to improve batch upload speed.",
            "source": "skipped_for_low_risk",
            "model": None,
        }

    return result


@app.get("/")
def root():
    return {
        "message": "Full-Stack Hybrid Fraud Detection Platform is running",
        "version": "3.0.0",
        "docs": "/docs",
        "features": [
            "signup/login",
            "single transaction scoring",
            "CSV upload scoring",
            "stored prediction history",
            "batch comparison",
            "LLM explanations",
        ],
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "fraud-platform-api"}


@app.post("/auth/signup")
def signup(request: SignupRequest):
    try:
        user = create_user(request.email, request.password)
        token = create_session(user["id"])
        return {"status": "success", "message": "Signup successful.", "token": token, "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/auth/login")
def login(request: LoginRequest):
    user = verify_user(request.email, request.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_session(user["id"])
    return {"status": "success", "message": "Login successful.", "token": token, "user": user}


@app.get("/auth/me")
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": user}


@app.post("/score", response_model=ScoreResponse)
def score_transaction(transaction: TransactionRequest):
    result = orchestrator.score_transaction(transaction)
    explanation = fraud_explanation_agent.explain(result)
    result["llm_explanation"] = explanation
    return result


@app.post("/uploads/predict-file")
async def predict_file(
    file: UploadFile = File(...),
    use_llm_for_approved: bool = False,
    user: Dict[str, Any] = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    content = await file.read()
    saved_path = save_uploaded_file(user["id"], file.filename, content)

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Could not read CSV. Please save file as UTF-8 CSV.")

    reader = csv.DictReader(io.StringIO(decoded))

    required_columns = {
        "transaction_id",
        "user_id",
        "device_id",
        "card_id",
        "ip_address",
        "merchant_id",
        "amount",
        "timestamp",
        "channel",
        "country",
    }

    missing_columns = required_columns - set(reader.fieldnames or [])
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {sorted(list(missing_columns))}",
        )

    raw_results = []
    display_results = []
    failed_rows = []

    approve_count = 0
    review_count = 0
    block_count = 0
    total_risk = 0.0
    max_risk = 0.0
    min_risk = 1.0

    for row_number, row in enumerate(reader, start=1):
        try:
            transaction = TransactionRequest(
                transaction_id=str(row["transaction_id"]).strip(),
                user_id=str(row["user_id"]).strip(),
                device_id=str(row["device_id"]).strip(),
                card_id=str(row["card_id"]).strip(),
                ip_address=str(row["ip_address"]).strip(),
                merchant_id=str(row["merchant_id"]).strip(),
                amount=float(row["amount"]),
                timestamp=str(row["timestamp"]).strip(),
                channel=str(row["channel"]).strip(),
                country=str(row["country"]).strip(),
            )

            result = orchestrator.score_transaction(transaction)
            result = add_explanation_for_bulk(result, use_llm_for_approved=use_llm_for_approved)

            decision = result.get("decision", "UNKNOWN")
            final_risk = float(result.get("final_risk", 0.0))

            if decision == "APPROVE":
                approve_count += 1
            elif decision == "REVIEW":
                review_count += 1
            elif decision == "BLOCK":
                block_count += 1

            total_risk += final_risk
            max_risk = max(max_risk, final_risk)
            min_risk = min(min_risk, final_risk)

            raw_results.append((row_number, result))

            display_results.append(
                {
                    "row_number": row_number,
                    "transaction_id": result.get("transaction_id"),
                    "decision": result.get("decision"),
                    "final_risk": result.get("final_risk"),
                    "gnn_graph_score": result.get("gnn_graph_score"),
                    "ml_score": result.get("ml_score"),
                    "llm_summary": result.get("llm_explanation", {}).get("summary", ""),
                }
            )

        except Exception as exc:
            failed_rows.append({"row_number": row_number, "error": str(exc), "row": row})

    successful_rows = len(raw_results)
    total_rows = successful_rows + len(failed_rows)

    if successful_rows == 0:
        min_risk = 0.0

    average_risk = round(total_risk / successful_rows, 4) if successful_rows > 0 else 0.0

    summary = {
        "total_rows": total_rows,
        "successful_rows": successful_rows,
        "failed_rows": len(failed_rows),
        "approve_count": approve_count,
        "review_count": review_count,
        "block_count": block_count,
        "average_risk": average_risk,
        "max_risk": round(max_risk, 4),
        "min_risk": round(min_risk, 4),
    }

    previous_batches = list_batches(user["id"], limit=1)

    batch_id = create_batch(
        user_id=user["id"],
        filename=file.filename,
        saved_path=saved_path,
        summary=summary,
    )

    for row_number, result in raw_results:
        save_prediction(user_id=user["id"], batch_id=batch_id, row_number=row_number, result=result)

    comparison = None
    if previous_batches:
        previous_batch_id = previous_batches[0]["id"]
        comparison = compare_batches(
            user_id=user["id"],
            current_batch_id=batch_id,
            previous_batch_id=previous_batch_id,
        )

    return {
        "status": "completed",
        "batch_id": batch_id,
        "filename": file.filename,
        "summary": summary,
        "comparison_with_previous_upload": comparison,
        "results": display_results,
        "failed_rows": failed_rows,
    }


@app.get("/uploads/history")
def upload_history(limit: int = 20, user: Dict[str, Any] = Depends(get_current_user)):
    return {"user": user, "batches": list_batches(user["id"], limit=limit)}


@app.get("/uploads/{batch_id}/predictions")
def batch_predictions(batch_id: int, limit: int = 500, user: Dict[str, Any] = Depends(get_current_user)):
    return {"batch_id": batch_id, "predictions": get_predictions(user["id"], batch_id, limit=limit)}


@app.get("/uploads/compare/{current_batch_id}/{previous_batch_id}")
def compare_uploads(
    current_batch_id: int,
    previous_batch_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
):
    try:
        return compare_batches(
            user_id=user["id"],
            current_batch_id=current_batch_id,
            previous_batch_id=previous_batch_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/feedback")
def submit_feedback(feedback: FeedbackRequest):
    return feedback_agent.save_feedback(
        transaction_id=feedback.transaction_id,
        analyst_label=feedback.analyst_label,
        analyst_notes=feedback.analyst_notes,
        reviewed_by=feedback.reviewed_by,
        extra=feedback.extra,
    )


@app.get("/feedback")
def list_feedback(limit: int = 20):
    return feedback_agent.list_feedback(limit=limit)


@app.get("/monitoring/summary")
def monitoring_summary(recent_limit: int = 100):
    return monitoring_agent.get_summary(recent_limit=recent_limit)


@app.get("/monitoring/drift")
def monitoring_drift(baseline_size: int = 100, recent_size: int = 25):
    return monitoring_agent.get_drift_report(baseline_size=baseline_size, recent_size=recent_size)


@app.post("/retrain")
def retrain(request: RetrainRequest):
    return retraining_agent.run_retraining(
        epochs=request.epochs,
        min_feedback=request.min_feedback,
        force=request.force,
    )


@app.get("/retrain/runs")
def retrain_runs(limit: int = 10):
    return retraining_agent.list_runs(limit=limit)


@app.on_event("shutdown")
def shutdown():
    orchestrator.close()
