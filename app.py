"""
Web Analyzer & Optimizer — Backend Flask
Analiza URLs públicas y genera soluciones descargables.
"""
import os
from pathlib import Path

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path, override=True)
except ImportError:
    pass
import re
import json
import uuid
import hashlib
import time
import logging
import requests
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file, g, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve

from analyzer import analizar, listar_analisis, _analizar_multipagina
from database import (
    init_db, create_user, authenticate, get_user_by_token,
    get_user_stats, increment_analyses, increment_downloads,
    create_shared_report, get_shared_report, track_event,
    add_monitored_url, get_monitored_urls, update_monitored_score, delete_monitored_url,
    has_submitted_feedback, set_receive_updates,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [
    "https://webanalyzer.com.ar",
    "https://www.webanalyzer.com.ar",
    "https://web-analyzer-1-l8uc.onrender.com",
    "http://127.0.0.1:5100",
    "http://localhost:5100",
]}})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri="memory://",
)

API_KEY = os.environ.get("ANALYZER_API_KEY", "")
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"

# --- Email: Resend (primario) + SMTP Ferozo (fallback) ---
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "a0110133.ferozo.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "no-reply@webanalyzer.com.ar")
SMTP_PASS = os.environ.get("SMTP_PASS", "25YmQhbaWJ")
SMTP_FROM = os.environ.get("SMTP_FROM", "Web Analyzer <no-reply@webanalyzer.com.ar>")

def send_email(to, subject, body):
    """Envia correo: Resend si hay API key, sino SMTP Ferozo."""

    # Intentar Resend primero (funciona desde Render)
    if RESEND_API_KEY:
        try:
            resp = __import__("requests").post(
                "https://api.resend.com/emails",
                json={
                    "from": SMTP_FROM,
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                log.info(f"Resend OK a {to}: {subject}")
                return True
            else:
                log.warning(f"Resend fallo ({resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            log.warning(f"Resend error: {e}")

    # Fallback: SMTP Ferozo
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart()
    msg["From"] = SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        ctx = __import__("ssl").create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15, context=ctx) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.sendmail(SMTP_USER, to, msg.as_string())
        log.info(f"Email enviado a {to}: {subject}")
        return True
    except Exception as e:
        log.error(f"Error al enviar email a {to}: {e}")
        return False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BASE_DIR / "analyzer.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("web-analyzer")

OUTPUT_DIR = BASE_DIR / "output"
ANALISIS_DIR = BASE_DIR / "analisis"
OUTPUT_DIR.mkdir(exist_ok=True)
ANALISIS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


@app.before_request
def check_auth():
    """Autenticación: API key global O token de usuario."""
    # Rutas públicas
    if request.path.startswith("/static") or request.path.startswith("/r/"):
        return None
    if request.path == "/" or request.path == "/api/health":
        return None
    if request.path in ("/api/auth/register", "/api/auth/login"):
        return None
    if request.path in ("/checkout-success",):
        return None

    # API key global (modo admin/dev)
    if API_KEY:
        auth = request.headers.get("Authorization", "")
        token_arg = request.args.get("token", "")
        if (auth.startswith("Bearer ") and auth[7:] == API_KEY) or (token_arg == API_KEY):
            return None

    # Token de usuario
    user_token = request.headers.get("X-User-Token", "") or request.args.get("user_token", "")
    if user_token:
        user = get_user_by_token(user_token)
        if user:
            g.current_user = user
            return None

    # Sin auth → acceso como invitado (tier free implícito)
    # Endpoints de descarga requieren autenticación
    if request.path.startswith("/api/download"):
        if DEV_MODE:
            return None
        return jsonify({"error": "Autenticación requerida", "code": "AUTH_REQUIRED"}), 401
    g.current_user = None
    return None


@app.before_request
def assign_trace_id():
    g.trace_id = uuid.uuid4().hex[:12]
    g.start_time = time.time()


@app.errorhandler(500)
def handle_500(e):
    """Devuelve JSON en vez de HTML para errores internos."""
    log.exception(f"trace={g.get('trace_id', '-')} 500 Internal Error")
    return jsonify({
        "error": "Error interno del servidor. Reintentá en unos segundos.",
        "code": "INTERNAL_ERROR",
        "trace_id": g.get('trace_id', ''),
    }), 500


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Ruta no encontrada", "code": "NOT_FOUND"}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": "Método no permitido", "code": "METHOD_NOT_ALLOWED"}), 405


@app.errorhandler(429)
def handle_429(e):
    return jsonify({"error": "Demasiadas solicitudes. Esperá un minuto.", "code": "RATE_LIMITED"}), 429


@app.after_request
def log_request(response):
    if request.path.startswith("/static"):
        return response
    duration_ms = int((time.time() - g.get("start_time", time.time())) * 1000)
    log.info(
        f"trace={g.get('trace_id', '-')} "
        f"method={request.method} path={request.path} "
        f"status={response.status_code} duration_ms={duration_ms}"
    )
    return response


# =============================================================================
# Rutas públicas (no requieren auth)
# =============================================================================


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/faq")
def faq_page():
    return render_template("faq.html")


@app.route("/features")
def features_page():
    return render_template("features.html")


@app.route("/r/<report_id>")
def shared_report(report_id):
    """Scorecard público compartible."""
    try:
        report = get_shared_report(report_id)
    except Exception:
        log.exception(f"Error cargando reporte {report_id}")
        report = None
    if not report:
        return render_template("report_404.html"), 404
    return render_template("report.html", report=report)


# =============================================================================
# Auth
# =============================================================================


@app.route("/api/auth/register", methods=["POST"])
@limiter.limit("10 per minute")
def api_register():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    if not email or not password:
        return jsonify({"error": "Email y contraseña requeridos"}), 400
    try:
        user = create_user(email, password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    if not user:
        return jsonify({"error": "El email ya está registrado"}), 409
    track_event("user_registered", user["id"])
    return jsonify({"email": user["email"], "tier": user["tier"]}), 201


@app.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per minute")
def api_login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()
    try:
        user = authenticate(email, password)
    except Exception as e:
        log.exception(f"trace={g.trace_id} Error en autenticación")
        return jsonify({"error": f"Error al iniciar sesión: {e}"}), 500
    if not user:
        return jsonify({"error": "Credenciales inválidas"}), 401
    track_event("user_logged_in", user["id"])
    return jsonify({
        "email": user["email"],
        "tier": user["tier"],
        "token": user["token"],
    })


@app.route("/api/auth/me")
def api_me():
    if not g.current_user:
        return jsonify({"tier": "free", "authenticated": False})
    user_id = g.current_user["id"]
    stats = get_user_stats(user_id)
    return jsonify({
        "email": g.current_user["email"],
        "tier": stats.get("tier", "free"),
        "analyses_count": stats.get("analyses_count", 0),
        "downloads_count": stats.get("downloads_count", 0),
        "receive_updates": bool(stats.get("receive_updates", False)),
        "authenticated": True,
    })


@app.route("/checkout-success")
def checkout_success():
    """Página de bienvenida post-registro/login."""
    return redirect("/?welcome=1", code=302)


# =============================================================================
# Feedback (reemplaza compras)
# =============================================================================


@app.route("/api/feedback", methods=["POST"])
@limiter.limit("10 per minute")
def api_feedback():
    """Encuesta corta antes de descargar. Requiere autenticacion."""
    if not g.current_user:
        return jsonify({"error": "Autenticacion requerida"}), 401

    data = request.get_json(force=True)
    report_hash = (data.get("report_hash") or "").strip()
    rating = data.get("rating")
    comentario = (data.get("comentario") or "").strip()[:200]
    recibir_updates = bool(data.get("recibir_updates", False))

    if not report_hash:
        return jsonify({"error": "report_hash requerido"}), 400
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "rating debe ser un numero entre 1 y 5"}), 400

    user_id = g.current_user["id"]

    try:
        track_event("feedback_submitted", user_id, "",
                    json.dumps({"report_hash": report_hash, "rating": rating, "comentario": comentario}))

        if recibir_updates:
            set_receive_updates(user_id, True)

        log.info(f"trace={g.trace_id} user={user_id} feedback rating={rating} hash={report_hash}")
    except Exception as e:
        log.exception("Error guardando feedback")
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True})


# =============================================================================
# Análisis
# =============================================================================


@app.route("/api/analyze", methods=["POST"])
@limiter.limit("5 per minute")
def api_analyze():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()

    if not url:
        return jsonify({"error": "URL requerida"}), 400

    if not url.startswith("http"):
        url = "https://" + url

    depth = int(data.get("depth", 1))
    log.info(f"trace={g.trace_id} url={url} depth={depth} Analizando")
    try:
        if depth > 1:
            resultado = _analizar_multipagina(url, depth)
        else:
            resultado = analizar(url)
    except Exception as e:
        log.exception(f"trace={g.trace_id} url={url} Error en análisis")
        return jsonify({"error": str(e)}), 500

    scores = resultado.get("scorecard", {})
    if scores:
        promedio = round(sum(s for s, _ in scores.values()) / len(scores), 1)
    else:
        promedio = 0

    report_hash = hashlib.sha256(url.encode()).hexdigest()[:12]
    user_id = g.current_user["id"] if g.current_user else None

    # DB operations son best-effort: si fallan, igual devolvemos el análisis
    try:
        create_shared_report(report_hash, url, {
            k: {"puntaje": s, "color": _color(s), "detalles": d}
            for k, (s, d) in scores.items()
        }, promedio)

        if user_id:
            increment_analyses(user_id)
            update_monitored_score(url, user_id, promedio)
        track_event("analysis_completed", user_id, url, json.dumps({"promedio": promedio}))
    except Exception as db_err:
        log.exception(f"trace={g.trace_id} url={url} Error guardando en DB (análisis igual se entrega)")

    # Todas las soluciones libres (sin pasarela de pago)
    soluciones = resultado.get("soluciones", [])
    soluciones_out = [
        {
            "nombre": s["nombre"],
            "tipo": s["tipo"],
            "descripcion": s["descripcion"],
            "path": s.get("path", ""),
            "bloqueado": False,
        }
        for s in soluciones
    ]

    return jsonify({
        "url": resultado["url"],
        "url_final": resultado.get("url_final", url),
        "fecha": resultado["fecha"],
        "scorecard": {k: {"puntaje": s, "color": _color(s), "detalles": d} for k, (s, d) in scores.items()},
        "promedio": promedio,
        "promedio_color": _color(promedio),
        "tecnologia": resultado.get("tecnologia", []),
        "meta": resultado.get("meta", {}),
        "imagenes": resultado.get("imagenes", {}),
        "headings": resultado.get("headings", {}),
        "forms": resultado.get("forms", {}),
        "scripts": resultado.get("scripts", {}),
        "size_kb": resultado.get("size_kb", 0),
        "psi": resultado.get("psi"),
        "hallazgos": resultado.get("hallazgos", []),
        "recomendaciones": resultado.get("recomendaciones", []),
        "soluciones": soluciones_out,
        "errores": resultado.get("errores", []),
        "report_hash": report_hash,
        "report_url": f"/r/{report_hash}",
        "paginas": resultado.get("paginas", []),
        "promedio_sitio": resultado.get("promedio_sitio", promedio),
    })


# =============================================================================
# Descarga (requiere tier pago)
# =============================================================================


@app.route("/api/download/<filename>")
@limiter.limit("30 per minute")
def api_download(filename):
    if not re.match(r'^[a-zA-Z0-9_.\-]+$', filename):
        return jsonify({"error": "Nombre de archivo inválido"}), 400

    report_hash = (request.args.get("report_hash") or "").strip()

    ext = os.path.splitext(filename)[1].lower()
    es_premium = ext in (".zip", ".json")

    # Premium (.zip, .json): requiere auth + feedback
    # No-premium (.html, .md, .liquid): libre
    if es_premium and not DEV_MODE:
        if not g.current_user:
            return jsonify({
                "error": "Autenticacion requerida para descargar",
                "code": "AUTH_REQUIRED",
            }), 401
        if report_hash and not has_submitted_feedback(g.current_user["id"], report_hash):
            return jsonify({
                "error": "Completa la encuesta para descargar",
                "action": "feedback_required",
            }), 403

    safe = os.path.basename(filename)
    path = (OUTPUT_DIR / safe).resolve()

    if not str(path).startswith(str(OUTPUT_DIR.resolve())):
        return jsonify({"error": "Acceso denegado"}), 403

    if not path.exists():
        return jsonify({"error": "Archivo no encontrado"}), 404

    user_id = g.current_user["id"] if g.current_user else None
    try:
        if user_id:
            increment_downloads(user_id)
        track_event("plugin_downloaded", user_id, filename)
    except Exception:
        log.exception("Error guardando estadísticas de descarga")

    return send_file(str(path), as_attachment=True, download_name=safe)


# =============================================================================
# Historial y health
# =============================================================================


@app.route("/api/monitor", methods=["GET", "POST", "DELETE"])
@limiter.limit("30 per minute")
def api_monitor():
    """GET: listar URLs monitoreadas. POST: agregar. DELETE: eliminar."""
    if not g.current_user or not g.current_user.get("id"):
        return jsonify({"error": "Requiere autenticación"}), 401

    user_id = g.current_user["id"]

    if request.method == "GET":
        urls = get_monitored_urls(user_id)
        return jsonify(urls)

    if request.method == "POST":
        data = request.get_json(force=True)
        url = (data.get("url") or "").strip()
        score = data.get("score", 0)
        if not url:
            return jsonify({"error": "URL requerida"}), 400
        monitor_id = add_monitored_url(url, user_id, score)
        if not monitor_id:
            # Ya existe: actualizar score
            update_monitored_score(url, user_id, score)
            return jsonify({"message": "Monitoreo actualizado"})
        return jsonify({"id": monitor_id, "message": "URL agregada al monitoreo"}), 201

    if request.method == "DELETE":
        monitor_id = request.args.get("id")
        if not monitor_id:
            return jsonify({"error": "ID requerido"}), 400
        ok = delete_monitored_url(int(monitor_id), user_id)
        if not ok:
            return jsonify({"error": "No encontrado"}), 404
        return jsonify({"message": "Monitoreo eliminado"})


@app.route("/api/history")
@limiter.limit("30 per minute")
def api_history():
    return jsonify(listar_analisis())


@app.route("/api/lead", methods=["POST"])
def api_lead():
    """Captura email del lead + scores y envía reporte completo."""
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip()
    url = (data.get("url") or "").strip()
    promedio = data.get("promedio")
    report_hash = data.get("report_hash", "")

    if not email or not url:
        return jsonify({"error": "Email y URL requeridos"}), 400

    # Guardar lead
    try:
        track_event("lead_captured", None, url,
            json.dumps({"email": email, "promedio": promedio, "report_hash": report_hash}))
        log.info(f"trace={g.trace_id} lead={email} url={url} score={promedio}")
    except Exception as e:
        log.exception("Error guardando lead")

    # Enviar reporte por email
    if report_hash:
        report_url = f"https://webanalyzer.com.ar/report/{report_hash}"
    else:
        report_url = url
    subject = "Tu analisis web esta listo"
    body = f"""Hola,

Tu analisis de {url} esta completo.

Puntaje general: {promedio}/10

Ver el reporte completo aca:
{report_url}

---
Web Analyzer
"""
    sent = send_email(email, subject, body)

    return jsonify({"ok": True, "sent": sent})

@app.route("/api/stats")
def api_stats():
    try:
        from database import get_public_stats
        return jsonify(get_public_stats())
    except Exception as e:
        log.exception("Error en /api/stats")
        return jsonify({"error": "Estadísticas no disponibles", "analyses": 0, "pages": 0, "users": 0}), 200


@app.route("/api/health")
def api_health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# =============================================================================
# Helpers
# =============================================================================


def _color(score):
    if score >= 8:
        return "verde"
    elif score >= 5:
        return "amarillo"
    return "rojo"


# =============================================================================
# Main
# =============================================================================


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5100))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")

    if not API_KEY:
        log.warning("ANALYZER_API_KEY no configurada — la API opera sin autenticación")

    print(f"\n{'='*55}")
    print(f"  Web Analyzer & Optimizer")
    print(f"  http://{host}:{port}")
    print(f"  Auth: {'configurada' if API_KEY else 'DESHABILITADA (set ANALYZER_API_KEY)'}")
    print(f"{'='*55}\n")

    serve(app, host=host, port=port)
