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
        load_dotenv(_env_path)
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

try:
    import mercadopago as _mp
except ImportError:
    _mp = None
from flask import Flask, render_template, request, jsonify, send_file, g, redirect
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve

from analyzer import analizar, listar_analisis, _analizar_multipagina
from database import (
    init_db, create_user, authenticate, get_user_by_token,
    upgrade_to_paid, get_user_stats, increment_analyses, increment_downloads,
    create_shared_report, get_shared_report, track_event,
    add_monitored_url, get_monitored_urls, update_monitored_score, delete_monitored_url,
    purchase_analysis, has_purchased, get_purchased_reports,
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
MP_ACCESS_TOKEN = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
MP_WEBHOOK_SECRET = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "")
PRICE_ARS = int(os.environ.get("PRICE_ARS", "12000"))
MP_SANDBOX = os.environ.get("MERCADOPAGO_SANDBOX", "false").lower() == "true"
DEV_MODE = os.environ.get("DEV_MODE", "").lower() == "true"

# --- SMTP para correos transaccionales ---
SMTP_HOST = os.environ.get("SMTP_HOST", "a0110133.ferozo.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ.get("SMTP_USER", "no-reply@webanalyzer.com.ar")
SMTP_PASS = os.environ.get("SMTP_PASS", "25YmQhbaWJ")
SMTP_FROM = os.environ.get("SMTP_FROM", "Web Analyzer <no-reply@webanalyzer.com.ar>")

def send_email(to, subject, body):
    """Envia un correo via SMTP (Ferozo/DonWeb)."""
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
    if request.path.startswith("/api/mercadopago"):
        return None
    if request.path in ("/checkout-success", "/activar-pro"):
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


@app.route("/activar-pro")
def activar_pro_page():
    return render_template("activar-pro.html", dev_mode=DEV_MODE)

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
    user = authenticate(email, password)
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
        "authenticated": True,
        "purchased_reports": get_purchased_reports(user_id),
    })


# =============================================================================
# Upgrade (MercadoPago Checkout Pro)
# =============================================================================


@app.route("/api/create-preference", methods=["POST"])
def api_create_preference():
    if not g.current_user:
        return jsonify({"error": "Debés iniciar sesión primero"}), 401
    if not _mp:
        return jsonify({"error": "MercadoPago: paquete no instalado."}), 500
    if not MP_ACCESS_TOKEN:
        return jsonify({"error": "MercadoPago: MERCADOPAGO_ACCESS_TOKEN no configurada."}), 500

    data = request.get_json(force=True)
    report_hash = (data.get("report_hash") or "").strip()
    if not report_hash:
        return jsonify({"error": "report_hash requerido"}), 400

    host = request.host_url.rstrip("/")
    # En producción detrás de reverse-proxy, Flask ve HTTP pero la URL
    # pública es HTTPS.  Detectamos vía X-Forwarded-Proto o ausencia de DEV_MODE.
    if not DEV_MODE or request.headers.get("X-Forwarded-Proto") == "https":
        host = host.replace("http://", "https://")

    preference_data = {
        "items": [{
            "title": "Web Analyzer — Análisis y descargas",
            "quantity": 1,
            "currency_id": "ARS",
            "unit_price": PRICE_ARS,
        }],
        "metadata": {
            "user_id": str(g.current_user["id"]),
            "report_hash": report_hash,
        },
        "external_reference": report_hash,
        "back_urls": {
            "success": host + "/checkout-success",
            "failure": host + "/",
            "pending": host + "/",
        },
        "auto_return": "approved",
    }
    # notification_url solo en producción (no en desarrollo local)
    if not DEV_MODE:
        preference_data["notification_url"] = host + "/api/mercadopago-webhook"

    try:
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        if MP_SANDBOX:
            headers["X-Sandbox"] = "true"
        r = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            json=preference_data,
            headers=headers,
            timeout=15,
        )
        pref = r.json()
        if r.status_code >= 400:
            log.error(f"MP API error {r.status_code}: {pref}")
            return jsonify({"error": f"MercadoPago: {pref.get('message', pref.get('error', 'error desconocido'))}"}), 500
        init_point = pref.get("sandbox_init_point") if MP_SANDBOX else pref.get("init_point", "")
        if not init_point:
            init_point = pref.get("sandbox_init_point") or pref.get("init_point", "")
        if init_point:
            return jsonify({"url": init_point, "preference_id": pref.get("id")})
        log.error(f"MP preference sin init_point: {pref}")
        return jsonify({"error": f"No se pudo crear la preferencia. MP: {pref.get('message', pref)}"}), 500
    except Exception as e:
        log.exception("Error creando preferencia MercadoPago")
        return jsonify({"error": str(e)}), 500


def _validar_firma_mp() -> bool:
    """Valida la firma x-signature del webhook de MercadoPago."""
    if not MP_WEBHOOK_SECRET:
        log.error("MERCADOPAGO_WEBHOOK_SECRET no configurada — webhook rechazado")
        return False
    sig = request.headers.get("x-signature", "")
    if not sig:
        log.warning("Webhook MP: falta header x-signature")
        return False
    try:
        import hmac
        parts = dict(p.split("=", 1) for p in sig.split(","))
        ts = parts.get("ts", "")
        v1 = parts.get("v1", "")
        body = request.get_data(as_text=True)
        expected = hmac.new(
            MP_WEBHOOK_SECRET.encode(),
            f"ts={ts}.{body}".encode(),
            "sha256",
        ).hexdigest()
        return hmac.compare_digest(v1, expected)
    except Exception:
        log.exception("Error validando firma MP")
        return False


@app.route("/api/mercadopago-webhook", methods=["POST"])
@limiter.limit("20 per minute")
def api_mercadopago_webhook():
    if not _validar_firma_mp():
        return jsonify({"error": "Firma invalida"}), 403

    data = request.get_json(force=True)
    log.info(f"Webhook MP recibido: action={data.get('action', '?')}")

    if not MP_ACCESS_TOKEN:
        log.warning("MERCADOPAGO_ACCESS_TOKEN no configurada")
        return jsonify({"error": "Webhook no configurado"}), 400

    payment_id = data.get("data", {}).get("id") or data.get("payment_id")
    if not payment_id:
        log.warning("Webhook MP sin payment_id")
        return jsonify({"error": "payment_id faltante"}), 400

    try:
        sdk = _mp.SDK(MP_ACCESS_TOKEN)
        result = sdk.payment().get(payment_id)
        payment = result.get("response", result)
        status = payment.get("status", "")
        metadata = payment.get("metadata") or {}
        user_id = metadata.get("user_id")
        report_hash = metadata.get("report_hash")

        if not user_id or not report_hash:
            pref_id = payment.get("preference_id", "")
            order = payment.get("order") or payment.get("merchant_order") or {}
            if not pref_id and order:
                pref_id = order.get("preference_id", "")
            if pref_id:
                pref_result = sdk.preference().get(pref_id)
                pref = pref_result.get("response", pref_result)
                pref_meta = pref.get("metadata") or {}
                user_id = user_id or pref_meta.get("user_id")
                report_hash = report_hash or pref_meta.get("report_hash")

        if status == "approved" and user_id and report_hash:
            if purchase_analysis(int(user_id), report_hash, payment_id):
                track_event("analysis_purchased", int(user_id), "", report_hash)
                log.info(f"Usuario {user_id} compro analisis {report_hash} via webhook")
            else:
                log.info(f"Compra duplicada: user={user_id} report={report_hash}")
        else:
            log.info(f"Webhook MP pago {payment_id}: status={status}")

    except Exception as e:
        log.exception("Error procesando webhook MP")
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "ok"})


@app.route("/api/force-upgrade")
def api_force_upgrade():
    """Solo para testing — activa PRO manualmente al usuario actual."""
    if not DEV_MODE:
        return jsonify({"error": "No disponible en producción"}), 403
    if not g.current_user:
        return jsonify({"error": "Iniciá sesión primero"}), 401
    upgrade_to_paid(g.current_user["id"])
    track_event("user_upgraded", g.current_user["id"])
    return jsonify({"tier": "paid", "message": "PRO activado manualmente"})


@app.route("/checkout-success")
def checkout_success():
    # MP Checkout Pro redirige con: collection_id, collection_status, preference_id, external_reference, payment_id
    payment_id = request.args.get("payment_id") or request.args.get("collection_id", "")
    status = request.args.get("status") or request.args.get("collection_status", "")
    preference_id = request.args.get("preference_id", "")
    external_ref = request.args.get("external_reference", "")
    purchased = False
    report_hash = ""
    analyze_url = ""

    if _mp and MP_ACCESS_TOKEN and status == "approved":
        sdk = _mp.SDK(MP_ACCESS_TOKEN)
        payment = None

        try:
            if payment_id:
                result = sdk.payment().get(payment_id)
                payment = result.get("response", result)
        except Exception:
            pass

        if not payment and external_ref:
            try:
                search = sdk.payment().search({"external_reference": external_ref})
                results = search.get("response", {}).get("results", [])
                if results:
                    payment = results[0]
                    payment_id = payment.get("id", payment_id)
            except Exception as e:
                log.warning(f"Error buscando pago MP en success: {e}")

        if payment:
            try:
                metadata = payment.get("metadata") or {}
                user_id = metadata.get("user_id")
                report_hash = metadata.get("report_hash")
                if user_id and report_hash and payment.get("status") == "approved":
                    purchase_analysis(int(user_id), report_hash, payment_id)
                    track_event("analysis_purchased", int(user_id), "", report_hash)
                    log.info(f"Usuario {user_id} compro analisis {report_hash} (success page)")
                    purchased = True
                    # Obtener la URL analizada para redirigir al usuario a sus resultados
                    shared = get_shared_report(report_hash)
                    if shared:
                        analyze_url = shared.get("url", "")
            except Exception as e:
                log.warning(f"Error registrando compra en success: {e}")

    if purchased and analyze_url:
        from urllib.parse import quote
        return redirect(f"/?analyze_url={quote(analyze_url, safe='')}&purchased=1", code=302)

    return render_template("checkout-success.html", payment_id=payment_id, upgraded=purchased, report_hash=report_hash)


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
    user_tier = g.current_user["tier"] if g.current_user else "free"

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

    purchased = user_id and (user_tier == "paid" or _has_purchased_safe(user_id, report_hash))

    soluciones = resultado.get("soluciones", [])
    soluciones_out = [
        {
            "nombre": s["nombre"],
            "tipo": s["tipo"],
            "descripcion": s["descripcion"],
            "path": s.get("path", ""),
            "bloqueado": not purchased and s["tipo"] in ("zip", "json"),
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
        "purchased": purchased,
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

    # Verificar compra: tier 'paid' (legacy) O compró este análisis
    # En modo desarrollo (local) las descargas están liberadas
    # Solo .zip y .json requieren pago; .html, .md, .liquid son gratis
    has_access = DEV_MODE
    if not has_access and g.current_user:
        if g.current_user.get("tier") == "paid":
            has_access = True
        elif report_hash and _has_purchased_safe(g.current_user["id"], report_hash):
            has_access = True

    if es_premium and not has_access:
        return jsonify({
            "error": "Descarga exclusiva — comprá el análisis por ARS 12.000",
            "action": "purchase",
        }), 402

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


def _has_purchased_safe(user_id, report_hash):
    try:
        return has_purchased(user_id, report_hash)
    except Exception:
        return False


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
