import hashlib
import secrets
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr


DB_PATH = Path("storage/fraud_platform_v1.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


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


def init_auth_db():
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

    conn.commit()
    conn.close()


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
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


@auth_router.post("/signup")
def signup(payload: SignupRequest):
    init_auth_db()

    email = payload.email.lower().strip()
    password = payload.password

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,),
    ).fetchone()

    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists. Please login.")

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


@auth_router.post("/login")
def login(payload: LoginRequest):
    init_auth_db()

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
        raise HTTPException(status_code=401, detail="Invalid email or password")

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


@auth_router.get("/me")
def me(user: Dict[str, Any] = Header(default=None)):
    return {"status": "ok"}