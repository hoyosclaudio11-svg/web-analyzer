"""
Base de datos y modelo de usuarios para Web Analyzer.
"""
import os
import re
import json
import time
import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from threading import local

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "analyzer.db"

# Asegurar directorio
DB_PATH.parent.mkdir(exist_ok=True)

# Conexiones thread-safe
_local = local()


def _conn():
    if not hasattr(_local, "db"):
        _local.db = sqlite3.connect(str(DB_PATH))
        _local.db.row_factory = sqlite3.Row
        _local.db.execute("PRAGMA journal_mode=WAL")
        _local.db.execute("PRAGMA foreign_keys=ON")
    return _local.db


def init_db():
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            tier TEXT NOT NULL DEFAULT 'free',
            token TEXT UNIQUE,
            token_expires TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_login TEXT,
            analyses_count INTEGER DEFAULT 0,
            downloads_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS shared_reports (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            scorecard_json TEXT NOT NULL,
            promedio REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            views INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event TEXT NOT NULL,
            user_id INTEGER,
            url TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics_events(event);
        CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at);
        CREATE INDEX IF NOT EXISTS idx_shared_url ON shared_reports(url);

        CREATE TABLE IF NOT EXISTS monitored_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            user_id INTEGER,
            last_score REAL,
            alerts_enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            last_checked TEXT,
            UNIQUE(url, user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_monitored_user ON monitored_urls(user_id);
    """)
    c.commit()


# =============================================================================
# Password hashing
# =============================================================================

_SALT = os.environ.get("ANALYZER_SALT", "analyzer-default-salt-change-me").encode()


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(8)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"pbkdf2:sha256:100000:{salt}:{dk.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        _, algo, iters, salt, dk_hex = stored.split(":")
        dk = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), int(iters))
        return dk.hex() == dk_hex
    except (ValueError, AttributeError):
        return False


# =============================================================================
# Operaciones de usuario
# =============================================================================

def create_user(email: str, password: str) -> dict | None:
    """Crea un usuario. Retorna dict o None si ya existe."""
    c = _conn()
    email = email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValueError("Email inválido")
    if len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres")

    pw_hash = _hash_password(password)
    try:
        cur = c.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, pw_hash))
        c.commit()
        return {"id": cur.lastrowid, "email": email, "tier": "free"}
    except sqlite3.IntegrityError:
        return None


def authenticate(email: str, password: str) -> dict | None:
    """Login. Retorna dict con token y datos de usuario o None."""
    c = _conn()
    email = email.strip().lower()
    row = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        return None
    if not _verify_password(password, row["password_hash"]):
        return None

    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    c.execute(
        "UPDATE users SET token = ?, token_expires = ?, last_login = datetime('now') WHERE id = ?",
        (token, expires, row["id"]),
    )
    c.commit()
    return {"id": row["id"], "email": row["email"], "tier": row["tier"], "token": token}


def get_user_by_token(token: str) -> dict | None:
    """Valida token y retorna datos de usuario o None."""
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE token = ?", (token,)).fetchone()
    if not row:
        return None
    if row["token_expires"] and datetime.fromisoformat(row["token_expires"]) < datetime.utcnow():
        return None
    return dict(row)


def upgrade_to_paid(user_id: int) -> dict:
    """Sube el tier del usuario a 'paid'."""
    c = _conn()
    c.execute("UPDATE users SET tier = 'paid' WHERE id = ?", (user_id,))
    c.commit()
    return {"id": user_id, "tier": "paid"}


def get_user_stats(user_id: int) -> dict:
    c = _conn()
    row = c.execute("SELECT tier, analyses_count, downloads_count, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else {}


def increment_analyses(user_id: int) -> None:
    c = _conn()
    c.execute("UPDATE users SET analyses_count = analyses_count + 1 WHERE id = ?", (user_id,))
    c.commit()


def increment_downloads(user_id: int) -> None:
    c = _conn()
    c.execute("UPDATE users SET downloads_count = downloads_count + 1 WHERE id = ?", (user_id,))
    c.commit()


# =============================================================================
# Reportes compartibles
# =============================================================================

def create_shared_report(report_id: str, url: str, scorecard: dict, promedio: float) -> str:
    c = _conn()
    c.execute(
        "INSERT OR IGNORE INTO shared_reports (id, url, scorecard_json, promedio) VALUES (?, ?, ?, ?)",
        (report_id, url, json.dumps(scorecard, ensure_ascii=False), promedio),
    )
    c.commit()
    return report_id


def get_shared_report(report_id: str) -> dict | None:
    c = _conn()
    row = c.execute("SELECT * FROM shared_reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        return None
    c.execute("UPDATE shared_reports SET views = views + 1 WHERE id = ?", (report_id,))
    c.commit()
    return {
        "id": row["id"],
        "url": row["url"],
        "scorecard": json.loads(row["scorecard_json"]),
        "promedio": row["promedio"],
        "created_at": row["created_at"],
        "views": row["views"] + 1,
    }


# =============================================================================
# Analytics
# =============================================================================

def add_monitored_url(url: str, user_id: int, score: float = 0) -> int | None:
    """Agrega una URL para monitoreo. Retorna id o None si ya existe."""
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO monitored_urls (url, user_id, last_score) VALUES (?, ?, ?)",
            (url, user_id, score),
        )
        c.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_monitored_urls(user_id: int) -> list[dict]:
    """Retorna las URLs monitoreadas por un usuario."""
    c = _conn()
    rows = c.execute(
        "SELECT * FROM monitored_urls WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_monitored_score(url: str, user_id: int, score: float) -> None:
    """Actualiza el último score de una URL monitoreada."""
    c = _conn()
    c.execute(
        "UPDATE monitored_urls SET last_score = ?, last_checked = datetime('now') WHERE url = ? AND user_id = ?",
        (score, url, user_id),
    )
    c.commit()


def delete_monitored_url(monitor_id: int, user_id: int) -> bool:
    """Elimina una URL del monitoreo. Retorna True si se eliminó."""
    c = _conn()
    cur = c.execute("DELETE FROM monitored_urls WHERE id = ? AND user_id = ?", (monitor_id, user_id))
    c.commit()
    return cur.rowcount > 0


def get_public_stats() -> dict:
    """Estadísticas públicas para mostrar en la landing page."""
    c = _conn()
    total_analyses = c.execute("SELECT COUNT(*) FROM analytics_events WHERE event = 'analysis_completed'").fetchone()[0]
    total_downloads = c.execute("SELECT COUNT(*) FROM analytics_events WHERE event = 'plugin_downloaded'").fetchone()[0]
    total_reports = c.execute("SELECT COUNT(*) FROM shared_reports").fetchone()[0]
    return {
        "analyses": total_analyses,
        "downloads": total_downloads,
        "reports": total_reports,
    }


def track_event(event: str, user_id: int | None = None, url: str = "", metadata: str = ""):
    c = _conn()
    c.execute(
        "INSERT INTO analytics_events (event, user_id, url, metadata) VALUES (?, ?, ?, ?)",
        (event, user_id, url, metadata),
    )
    c.commit()


# Inicializar al importar
init_db()
