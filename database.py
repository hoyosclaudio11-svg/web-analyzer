"""
Base de datos y modelo de usuarios para Web Analyzer.
Soporta PostgreSQL (produccion) y SQLite (desarrollo local).
"""
import os
import re
import json
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from threading import local

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "analyzer.db"
DATABASE_URL = os.environ.get("DATABASE_URL", "")

_local = local()

# ---------------------------------------------------------------------------
# Motor: PostgreSQL si DATABASE_URL esta seteada, sino SQLite
# ---------------------------------------------------------------------------
PG = bool(DATABASE_URL)

if PG:
    import psycopg2
    import psycopg2.extras

    # Limpiar parámetros que psycopg2 no reconoce
    _PG_URL = DATABASE_URL
    for _bad in ("channel_binding",):
        _PG_URL = _PG_URL.replace(f"&{_bad}=require", "").replace(f"?{_bad}=require&", "?")

    def _conn():
        if not hasattr(_local, "db"):
            _local.db = psycopg2.connect(_PG_URL)
            _local.db.cursor_factory = psycopg2.extras.RealDictCursor
        return _local.db

    _PLACEHOLDER = "%s"
    _AUTO_ID = "SERIAL PRIMARY KEY"
    _NOW = "NOW()"
    _INSERT_OR_IGNORE = "ON CONFLICT DO NOTHING"
    _BOOLEAN = "BOOLEAN"
    _REAL = "DOUBLE PRECISION"

    def _lastrowid(cur, table, col="id"):
        """PostgreSQL no tiene lastrowid; usamos RETURNING."""
        # Para INSERT con RETURNING, el caller debe manejar distinto
        return None

    def _exec_insert(c, sql, params, returning="id"):
        """Ejecuta INSERT con RETURNING y retorna el id."""
        if "RETURNING" not in sql:
            sql = sql.rstrip(";") + f" RETURNING {returning}"
        c.execute(sql, params)
        row = c.fetchone()
        return row[returning] if row else None

else:
    import sqlite3
    DB_PATH.parent.mkdir(exist_ok=True)

    def _conn():
        if not hasattr(_local, "db"):
            _local.db = sqlite3.connect(str(DB_PATH))
            _local.db.row_factory = sqlite3.Row
            _local.db.execute("PRAGMA journal_mode=WAL")
            _local.db.execute("PRAGMA foreign_keys=ON")
        return _local.db

    _PLACEHOLDER = "?"
    _AUTO_ID = "INTEGER PRIMARY KEY AUTOINCREMENT"
    _NOW = "datetime('now')"
    _INSERT_OR_IGNORE = "OR IGNORE"
    _BOOLEAN = "INTEGER"
    _REAL = "REAL"

    def _lastrowid(cur, table=None, col=None):
        return cur.lastrowid

    def _exec_insert(c, sql, params, returning="id"):
        """SQLite: usa lastrowid."""
        c.execute(sql, params)
        return c.lastrowid


def _q(n=1):
    """Retorna placeholder(s) segun el motor."""
    p = _PLACEHOLDER
    return p if n == 1 else ", ".join(p for _ in range(n))


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db():
    c = _conn()
    if PG:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'free',
                token TEXT UNIQUE,
                token_expires TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_login TIMESTAMPTZ,
                analyses_count INTEGER DEFAULT 0,
                downloads_count INTEGER DEFAULT 0
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS shared_reports (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                scorecard_json TEXT NOT NULL,
                promedio DOUBLE PRECISION,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                views INTEGER DEFAULT 0
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id SERIAL PRIMARY KEY,
                event TEXT NOT NULL,
                user_id INTEGER,
                url TEXT,
                metadata TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics_events(event);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_analytics_created ON analytics_events(created_at);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_shared_url ON shared_reports(url);")
        c.execute("""
            CREATE TABLE IF NOT EXISTS monitored_urls (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                user_id INTEGER,
                last_score DOUBLE PRECISION,
                alerts_enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                last_checked TIMESTAMPTZ,
                UNIQUE(url, user_id)
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_monitored_user ON monitored_urls(user_id);")
        c.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                report_hash TEXT NOT NULL,
                payment_id TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(user_id, report_hash)
            );
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);")
        c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_report ON purchases(report_hash);")
    else:
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

            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_hash TEXT NOT NULL,
                payment_id TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, report_hash)
            );

            CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
            CREATE INDEX IF NOT EXISTS idx_purchases_report ON purchases(report_hash);
        """)
    c.commit()


# =============================================================================
# Password hashing
# =============================================================================

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
    c = _conn()
    email = email.strip().lower()
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        raise ValueError("Email invalido")
    if len(password) < 6:
        raise ValueError("La contrasena debe tener al menos 6 caracteres")

    pw_hash = _hash_password(password)
    try:
        if PG:
            uid = _exec_insert(
                c,
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, pw_hash),
            )
        else:
            cur = c.execute(
                f"INSERT INTO users (email, password_hash) VALUES ({_q()}, {_q()})",
                (email, pw_hash),
            )
            uid = cur.lastrowid
        c.commit()
        return {"id": uid, "email": email, "tier": "free"}
    except (psycopg2.errors.UniqueViolation if PG else sqlite3.IntegrityError):
        c.rollback() if PG else None
        return None
    except Exception:
        # Fallback para otros motores o si psycopg2 no esta en scope
        try:
            c.rollback() if PG else None
        except Exception:
            pass
        return None


def authenticate(email: str, password: str) -> dict | None:
    c = _conn()
    email = email.strip().lower()
    row = c.execute(f"SELECT * FROM users WHERE email = {_q()}", (email,)).fetchone()
    if not row:
        return None
    if not _verify_password(password, row["password_hash"]):
        return None

    token = secrets.token_hex(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    c.execute(
        f"UPDATE users SET token = {_q()}, token_expires = {_q()}, last_login = {_NOW} WHERE id = {_q()}",
        (token, expires, row["id"]),
    )
    c.commit()
    return {"id": row["id"], "email": row["email"], "tier": row["tier"], "token": token}


def get_user_by_token(token: str) -> dict | None:
    c = _conn()
    row = c.execute(f"SELECT * FROM users WHERE token = {_q()}", (token,)).fetchone()
    if not row:
        return None
    if row["token_expires"] and datetime.fromisoformat(row["token_expires"]) < datetime.utcnow():
        return None
    return dict(row)


def upgrade_to_paid(user_id: int) -> dict:
    c = _conn()
    c.execute(f"UPDATE users SET tier = 'paid' WHERE id = {_q()}", (user_id,))
    c.commit()
    return {"id": user_id, "tier": "paid"}


def get_user_stats(user_id: int) -> dict:
    c = _conn()
    row = c.execute(
        f"SELECT tier, analyses_count, downloads_count, created_at FROM users WHERE id = {_q()}",
        (user_id,),
    ).fetchone()
    return dict(row) if row else {}


def increment_analyses(user_id: int) -> None:
    c = _conn()
    c.execute(f"UPDATE users SET analyses_count = analyses_count + 1 WHERE id = {_q()}", (user_id,))
    c.commit()


def increment_downloads(user_id: int) -> None:
    c = _conn()
    c.execute(f"UPDATE users SET downloads_count = downloads_count + 1 WHERE id = {_q()}", (user_id,))
    c.commit()


# =============================================================================
# Compras por analisis (MercadoPago)
# =============================================================================

def purchase_analysis(user_id: int, report_hash: str, payment_id: str = "") -> bool:
    c = _conn()
    try:
        if PG:
            c.execute(
                "INSERT INTO purchases (user_id, report_hash, payment_id) VALUES (%s, %s, %s) ON CONFLICT (user_id, report_hash) DO NOTHING",
                (user_id, report_hash, payment_id),
            )
        else:
            c.execute(
                f"INSERT OR IGNORE INTO purchases (user_id, report_hash, payment_id) VALUES ({_q()}, {_q()}, {_q()})",
                (user_id, report_hash, payment_id),
            )
        c.commit()
        if c.rowcount == 0:
            return False
        increment_analyses(user_id)
        return True
    except Exception:
        try:
            c.rollback() if PG else None
        except Exception:
            pass
        return False


def has_purchased(user_id: int, report_hash: str) -> bool:
    c = _conn()
    row = c.execute(
        f"SELECT 1 FROM purchases WHERE user_id = {_q()} AND report_hash = {_q()}",
        (user_id, report_hash),
    ).fetchone()
    return row is not None


def get_purchased_reports(user_id: int) -> list[str]:
    c = _conn()
    rows = c.execute(
        f"SELECT report_hash FROM purchases WHERE user_id = {_q()} ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [r["report_hash"] for r in rows]


# =============================================================================
# Reportes compartibles
# =============================================================================

def create_shared_report(report_id: str, url: str, scorecard: dict, promedio: float) -> str:
    c = _conn()
    if PG:
        c.execute(
            "INSERT INTO shared_reports (id, url, scorecard_json, promedio) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (report_id, url, json.dumps(scorecard, ensure_ascii=False), promedio),
        )
    else:
        c.execute(
            f"INSERT OR IGNORE INTO shared_reports (id, url, scorecard_json, promedio) VALUES ({_q()}, {_q()}, {_q()}, {_q()})",
            (report_id, url, json.dumps(scorecard, ensure_ascii=False), promedio),
        )
    c.commit()
    return report_id


def get_shared_report(report_id: str) -> dict | None:
    c = _conn()
    row = c.execute(f"SELECT * FROM shared_reports WHERE id = {_q()}", (report_id,)).fetchone()
    if not row:
        return None
    c.execute(f"UPDATE shared_reports SET views = views + 1 WHERE id = {_q()}", (report_id,))
    c.commit()
    return {
        "id": row["id"],
        "url": row["url"],
        "scorecard": json.loads(row["scorecard_json"]),
        "promedio": row["promedio"],
        "created_at": str(row["created_at"]),
        "views": row["views"] + 1,
    }


# =============================================================================
# Monitoreo
# =============================================================================

def add_monitored_url(url: str, user_id: int, score: float = 0) -> int | None:
    c = _conn()
    try:
        if PG:
            uid = _exec_insert(
                c,
                "INSERT INTO monitored_urls (url, user_id, last_score) VALUES (%s, %s, %s)",
                (url, user_id, score),
            )
        else:
            cur = c.execute(
                f"INSERT INTO monitored_urls (url, user_id, last_score) VALUES ({_q()}, {_q()}, {_q()})",
                (url, user_id, score),
            )
            uid = cur.lastrowid
        c.commit()
        return uid
    except (psycopg2.errors.UniqueViolation if PG else sqlite3.IntegrityError):
        c.rollback() if PG else None
        return None
    except Exception:
        return None


def get_monitored_urls(user_id: int) -> list[dict]:
    c = _conn()
    rows = c.execute(
        f"SELECT * FROM monitored_urls WHERE user_id = {_q()} ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def update_monitored_score(url: str, user_id: int, score: float) -> None:
    c = _conn()
    c.execute(
        f"UPDATE monitored_urls SET last_score = {_q()}, last_checked = {_NOW} WHERE url = {_q()} AND user_id = {_q()}",
        (score, url, user_id),
    )
    c.commit()


def delete_monitored_url(monitor_id: int, user_id: int) -> bool:
    c = _conn()
    cur = c.execute(
        f"DELETE FROM monitored_urls WHERE id = {_q()} AND user_id = {_q()}",
        (monitor_id, user_id),
    )
    c.commit()
    return cur.rowcount > 0


# =============================================================================
# Analytics
# =============================================================================

def get_public_stats() -> dict:
    c = _conn()
    total_analyses = c.execute(
        "SELECT COUNT(*) FROM analytics_events WHERE event = 'analysis_completed'"
    ).fetchone()["count"]
    total_downloads = c.execute(
        "SELECT COUNT(*) FROM analytics_events WHERE event = 'plugin_downloaded'"
    ).fetchone()["count"]
    total_reports = c.execute("SELECT COUNT(*) FROM shared_reports").fetchone()["count"]
    return {
        "analyses": total_analyses,
        "downloads": total_downloads,
        "reports": total_reports,
    }


def track_event(event: str, user_id: int | None = None, url: str = "", metadata: str = ""):
    c = _conn()
    c.execute(
        f"INSERT INTO analytics_events (event, user_id, url, metadata) VALUES ({_q()}, {_q()}, {_q()}, {_q()})",
        (event, user_id, url, metadata),
    )
    c.commit()


# Inicializar al importar
init_db()
