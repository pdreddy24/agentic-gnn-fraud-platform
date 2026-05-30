import csv
import hashlib
import io
import secrets
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from app.schemas.transaction_schema import TransactionRequest, ScoreResponse
from app.schemas.feedback_schema import FeedbackRequest, RetrainRequest

from app.agents.triage_orchestrator_agent import TriageOrchestratorAgent
from app.agents.feedback_agent import FeedbackAgent
from app.agents.monitoring_agent import MonitoringAgent
from app.agents.retraining_agent import RetrainingAgent
from app.agents.fraud_explanation_agent import FraudExplanationAgent


app = FastAPI(
    title="Hybrid Fraud Detection Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DB_PATH = Path("storage/fraud_platform_v2.db")
UPLOAD_DIR = Path("uploads")

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


orchestrator = TriageOrchestratorAgent()
feedback_agent = FeedbackAgent()
monitoring_agent = MonitoringAgent()
retraining_agent = RetrainingAgent()
fraud_explanation_agent = FraudExplanationAgent()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db():
    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            saved_path TEXT NOT NULL,
            total_rows INTEGER DEFAULT 0,
            successful_rows INTEGER DEFAULT 0,
            failed_rows INTEGER DEFAULT 0,
            approve_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 0,
            block_count INTEGER DEFAULT 0,
            average_risk REAL DEFAULT 0,
            max_risk REAL DEFAULT 0,
            min_risk REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            batch_id INTEGER NOT NULL,
            row_number INTEGER NOT NULL,
            transaction_id TEXT,
            decision TEXT,
            final_risk REAL,
            gnn_graph_score REAL,
            ml_score REAL,
            llm_summary TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing login token")

    parts = authorization.split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = parts[1]

    conn = get_db()

    user = conn.execute(
        """
        SELECT user_id, email
        FROM sessions
        WHERE token = ?
        """,
        (token,),
    ).fetchone()

    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired login token")

    return {
        "id": user["user_id"],
        "email": user["email"],
    }


@app.get("/")
def root():
    return {
        "message": "Hybrid Fraud Detection Platform API is running",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
    }


@app.post("/auth/signup")
def signup(payload: SignupRequest):
    email = payload.email.lower().strip()
    password = payload.password

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters",
        )

    conn = get_db()

    existing_user = conn.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()

    if existing_user:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="User already exists. Please login.",
        )

    password_hash = hash_password(password)

    cursor = conn.execute(
        """
        INSERT INTO users (email, password_hash)
        VALUES (?, ?)
        """,
        (email, password_hash),
    )

    user_id = cursor.lastrowid
    token = secrets.token_hex(32)

    conn.execute(
        """
        INSERT INTO sessions (token, user_id, email)
        VALUES (?, ?, ?)
        """,
        (token, user_id, email),
    )

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Signup successful",
        "token": token,
        "user": {
            "id": user_id,
            "email": email,
        },
    }


@app.post("/auth/login")
def login(payload: LoginRequest):
    email = payload.email.lower().strip()
    password_hash = hash_password(payload.password)

    conn = get_db()

    user = conn.execute(
        """
        SELECT id, email
        FROM users
        WHERE email = ? AND password_hash = ?
        """,
        (email, password_hash),
    ).fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = secrets.token_hex(32)

    conn.execute(
        """
        INSERT INTO sessions (token, user_id, email)
        VALUES (?, ?, ?)
        """,
        (token, user["id"], user["email"]),
    )

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
        },
    }


@app.get("/auth/me")
def me(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "status": "success",
        "user": user,
    }


@app.post("/score", response_model=ScoreResponse)
def score_transaction(transaction: TransactionRequest):
    result = orchestrator.score_transaction(transaction)
    explanation = fraud_explanation_agent.explain(result)
    result["llm_explanation"] = explanation
    return result


def save_uploaded_file(user_id: int, filename: str, content: bytes) -> str:
    user_upload_dir = UPLOAD_DIR / f"user_{user_id}"
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = filename.replace(" ", "_")
    saved_path = user_upload_dir / f"{secrets.token_hex(8)}_{safe_filename}"

    with open(saved_path, "wb") as file:
        file.write(content)

    return str(saved_path)


def add_explanation_for_bulk(
    result: Dict[str, Any],
    use_llm_for_approved: bool = False,
):
    decision = result.get("decision", "UNKNOWN")

    if decision in ["REVIEW", "BLOCK"] or use_llm_for_approved:
        result["llm_explanation"] = fraud_explanation_agent.explain(result)
    else:
        result["llm_explanation"] = {
            "summary": "Low-risk transaction approved. LLM explanation skipped for faster batch processing.",
            "risk_level": "LOW",
            "main_risk_factors": result.get("reason_codes", []),
            "recommended_actions": [
                "Approve transaction",
                "Continue normal monitoring",
            ],
            "source": "skipped_for_low_risk",
            "model": None,
        }

    return result


def save_prediction(
    user_id: int,
    batch_id: int,
    row_number: int,
    result: Dict[str, Any],
):
    conn = get_db()

    conn.execute(
        """
        INSERT INTO predictions (
            user_id,
            batch_id,
            row_number,
            transaction_id,
            decision,
            final_risk,
            gnn_graph_score,
            ml_score,
            llm_summary
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            batch_id,
            row_number,
            result.get("transaction_id"),
            result.get("decision"),
            float(result.get("final_risk", 0.0)),
            float(result.get("gnn_graph_score", 0.0)),
            float(result.get("ml_score", 0.0)),
            result.get("llm_explanation", {}).get("summary", ""),
        ),
    )

    conn.commit()
    conn.close()


@app.post("/uploads/predict-file")
async def predict_file(
    file: UploadFile = File(...),
    use_llm_for_approved: bool = False,
    user: Dict[str, Any] = Depends(get_current_user),
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file.",
        )

    content = await file.read()
    saved_path = save_uploaded_file(user["id"], file.filename, content)

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Could not read CSV. Please save your file as UTF-8 CSV.",
        )

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
            result = add_explanation_for_bulk(result, use_llm_for_approved)

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
                    "llm_summary": result.get("llm_explanation", {}).get(
                        "summary",
                        "",
                    ),
                }
            )

        except Exception as exc:
            failed_rows.append(
                {
                    "row_number": row_number,
                    "error": str(exc),
                    "row": row,
                }
            )

    successful_rows = len(raw_results)
    total_rows = successful_rows + len(failed_rows)

    if successful_rows == 0:
        min_risk = 0.0

    average_risk = (
        round(total_risk / successful_rows, 4)
        if successful_rows > 0
        else 0.0
    )

    conn = get_db()

    cursor = conn.execute(
        """
        INSERT INTO upload_batches (
            user_id,
            filename,
            saved_path,
            total_rows,
            successful_rows,
            failed_rows,
            approve_count,
            review_count,
            block_count,
            average_risk,
            max_risk,
            min_risk
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user["id"],
            file.filename,
            saved_path,
            total_rows,
            successful_rows,
            len(failed_rows),
            approve_count,
            review_count,
            block_count,
            average_risk,
            round(max_risk, 4),
            round(min_risk, 4),
        ),
    )

    batch_id = cursor.lastrowid

    conn.commit()
    conn.close()

    for row_number, result in raw_results:
        save_prediction(user["id"], batch_id, row_number, result)

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

    return {
        "status": "completed",
        "batch_id": batch_id,
        "filename": file.filename,
        "summary": summary,
        "results": display_results,
        "failed_rows": failed_rows,
    }


@app.get("/uploads/history")
def upload_history(
    limit: int = 20,
    user: Dict[str, Any] = Depends(get_current_user),
):
    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            id,
            filename,
            total_rows,
            successful_rows,
            failed_rows,
            approve_count,
            review_count,
            block_count,
            average_risk,
            max_risk,
            min_risk,
            created_at
        FROM upload_batches
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user["id"], limit),
    ).fetchall()

    conn.close()

    return {
        "user": user,
        "batches": [dict(row) for row in rows],
    }


@app.get("/uploads/{batch_id}/predictions")
def batch_predictions(
    batch_id: int,
    limit: int = 500,
    user: Dict[str, Any] = Depends(get_current_user),
):
    conn = get_db()

    rows = conn.execute(
        """
        SELECT
            id,
            row_number,
            transaction_id,
            decision,
            final_risk,
            gnn_graph_score,
            ml_score,
            llm_summary,
            created_at
        FROM predictions
        WHERE user_id = ? AND batch_id = ?
        ORDER BY row_number ASC
        LIMIT ?
        """,
        (user["id"], batch_id, limit),
    ).fetchall()

    conn.close()

    return {
        "batch_id": batch_id,
        "predictions": [dict(row) for row in rows],
    }


@app.get("/uploads/compare/{current_batch_id}/{previous_batch_id}")
def compare_uploads(
    current_batch_id: int,
    previous_batch_id: int,
    user: Dict[str, Any] = Depends(get_current_user),
):
    conn = get_db()

    current = conn.execute(
        """
        SELECT *
        FROM upload_batches
        WHERE id = ? AND user_id = ?
        """,
        (current_batch_id, user["id"]),
    ).fetchone()

    previous = conn.execute(
        """
        SELECT *
        FROM upload_batches
        WHERE id = ? AND user_id = ?
        """,
        (previous_batch_id, user["id"]),
    ).fetchone()

    conn.close()

    if not current or not previous:
        raise HTTPException(status_code=404, detail="Batch not found")

    current = dict(current)
    previous = dict(previous)

    return {
        "current_batch": current,
        "previous_batch": previous,
        "risk_change": round(
            current["average_risk"] - previous["average_risk"],
            4,
        ),
        "review_change": current["review_count"] - previous["review_count"],
        "block_change": current["block_count"] - previous["block_count"],
        "total_rows_change": current["total_rows"] - previous["total_rows"],
    }


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
    return monitoring_agent.get_drift_report(
        baseline_size=baseline_size,
        recent_size=recent_size,
    )


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