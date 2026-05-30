import json
import secrets
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DB_DIR = Path("storage")
DB_DIR.mkdir(exist_ok=True)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "fraud_platform.db"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS upload_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                saved_path TEXT,
                total_rows INTEGER NOT NULL,
                successful_rows INTEGER NOT NULL,
                failed_rows INTEGER NOT NULL,
                approve_count INTEGER NOT NULL,
                review_count INTEGER NOT NULL,
                block_count INTEGER NOT NULL,
                average_risk REAL NOT NULL,
                max_risk REAL NOT NULL,
                min_risk REAL NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                batch_id INTEGER NOT NULL,
                row_number INTEGER NOT NULL,
                transaction_id TEXT,
                final_risk REAL,
                decision TEXT,
                gnn_graph_score REAL,
                ml_score REAL,
                llm_summary TEXT,
                full_result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(batch_id) REFERENCES upload_batches(id)
            )
        """)

        conn.commit()


def hash_password(password: str, salt: Optional[str] = None) -> Dict[str, str]:
    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()

    return {"password_hash": password_hash, "salt": salt}


def create_user(email: str, password: str) -> Dict[str, Any]:
    email = email.strip().lower()

    if not email:
        raise ValueError("Email is required.")

    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")

    hashed = hash_password(password)

    with get_connection() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (email, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (email, hashed["password_hash"], hashed["salt"], utc_now()),
            )
            conn.commit()
            return {"id": cur.lastrowid, "email": email}
        except sqlite3.IntegrityError:
            raise ValueError("User already exists. Please login.")


def verify_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    email = email.strip().lower()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None:
        return None

    hashed = hash_password(password, row["salt"])

    if hashed["password_hash"] != row["password_hash"]:
        return None

    return {"id": row["id"], "email": row["email"]}


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO user_sessions (token, user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (token, user_id, utc_now()),
        )
        conn.commit()

    return token


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.email
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ?
            """,
            (token,),
        ).fetchone()

    if row is None:
        return None

    return {"id": row["id"], "email": row["email"]}


def save_uploaded_file(user_id: int, filename: str, content: bytes) -> str:
    safe_filename = filename.replace("\\", "_").replace("/", "_")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    user_upload_dir = UPLOAD_DIR / f"user_{user_id}"
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    saved_path = user_upload_dir / f"{timestamp}_{safe_filename}"
    saved_path.write_bytes(content)
    return str(saved_path)


def create_batch(user_id: int, filename: str, saved_path: str, summary: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO upload_batches (
                user_id, filename, saved_path,
                total_rows, successful_rows, failed_rows,
                approve_count, review_count, block_count,
                average_risk, max_risk, min_risk,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                filename,
                saved_path,
                int(summary.get("total_rows", 0)),
                int(summary.get("successful_rows", 0)),
                int(summary.get("failed_rows", 0)),
                int(summary.get("approve_count", 0)),
                int(summary.get("review_count", 0)),
                int(summary.get("block_count", 0)),
                float(summary.get("average_risk", 0.0)),
                float(summary.get("max_risk", 0.0)),
                float(summary.get("min_risk", 0.0)),
                utc_now(),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def save_prediction(user_id: int, batch_id: int, row_number: int, result: Dict[str, Any]) -> None:
    llm_summary = ""
    if isinstance(result.get("llm_explanation"), dict):
        llm_summary = result["llm_explanation"].get("summary", "")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO predictions (
                user_id, batch_id, row_number,
                transaction_id, final_risk, decision,
                gnn_graph_score, ml_score, llm_summary,
                full_result_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                batch_id,
                row_number,
                result.get("transaction_id"),
                float(result.get("final_risk", 0.0)),
                result.get("decision"),
                float(result.get("gnn_graph_score", 0.0)),
                float(result.get("ml_score", 0.0)),
                llm_summary,
                json.dumps(result, default=str),
                utc_now(),
            ),
        )
        conn.commit()


def list_batches(user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM upload_batches
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def get_batch(user_id: int, batch_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM upload_batches
            WHERE user_id = ? AND id = ?
            """,
            (user_id, batch_id),
        ).fetchone()

    return dict(row) if row else None


def get_predictions(user_id: int, batch_id: int, limit: int = 500) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM predictions
            WHERE user_id = ? AND batch_id = ?
            ORDER BY row_number ASC
            LIMIT ?
            """,
            (user_id, batch_id, limit),
        ).fetchall()

    return [dict(row) for row in rows]


def compare_batches(user_id: int, current_batch_id: int, previous_batch_id: int) -> Dict[str, Any]:
    current = get_batch(user_id, current_batch_id)
    previous = get_batch(user_id, previous_batch_id)

    if not current:
        raise ValueError("Current batch not found.")

    if not previous:
        raise ValueError("Previous batch not found.")

    def diff(key: str) -> float:
        return round(float(current.get(key, 0) or 0) - float(previous.get(key, 0) or 0), 4)

    previous_avg = float(previous.get("average_risk", 0) or 0)
    current_avg = float(current.get("average_risk", 0) or 0)

    risk_change_percent = 0.0
    if previous_avg > 0:
        risk_change_percent = round(((current_avg - previous_avg) / previous_avg) * 100, 2)

    return {
        "current_batch": current,
        "previous_batch": previous,
        "comparison": {
            "average_risk_change": diff("average_risk"),
            "average_risk_change_percent": risk_change_percent,
            "approve_count_change": int(diff("approve_count")),
            "review_count_change": int(diff("review_count")),
            "block_count_change": int(diff("block_count")),
            "successful_rows_change": int(diff("successful_rows")),
        },
    }
