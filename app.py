"""
Web Analyzer & Optimizer — Backend Flask
Analiza URLs públicas y genera soluciones descargables.
"""
import os
import re
import json
import uuid
import hashlib
import time
import logging
from datetime import datetime
from pathlib import Path

try:
    import stripe as _stripe
except ImportError:
    _stripe = None
from flask import Flask, render_template, request, jsonify, send_file, g
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
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri="memory://",
)

API_KEY = os.environ.get("ANALYZER_API_KEY", "")
STRIPE_SECRET = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
PRICE_USD = 12  # Precio one-shot del plan PRO
if _stripe and STRIPE_SECRET:
    _stripe.api_key = STRIPE_SECRET

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
    if request.path.startswith("/api/stripe"):
        return None
    if request.path == "/checkout-success":
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
    return render_template("index.html", api_key=API_KEY)


@app.route("/faq")
def faq_page():
    return render_template("faq.html")


@app.route("/features")
def features_page():
    return render_template("features.html")


@app.route("/r/<report_id>")
def shared_report(report_id):
    """Scorecard público compartible."""
    report = get_shared_report(report_id)
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
    stats = get_user_stats(g.current_user["id"])
    return jsonify({
        "email": g.current_user["email"],
        "tier": stats.get("tier", "free"),
        "analyses_count": stats.get("analyses_count", 0),
        "downloads_count": stats.get("downloads_count", 0),
        "authenticated": True,
    })


# =============================================================================
# Upgrade (Stripe Checkout)
# =============================================================================


@app.route("/api/create-checkout-session", methods=["POST"])
def api_create_checkout():
    if not g.current_user:
        return jsonify({"error": "Debés iniciar sesión primero"}), 401
    if not _stripe:
        return jsonify({"error": "Stripe: paquete no instalado. Ejecutá pip install stripe en el servidor."}), 500
    if not STRIPE_SECRET:
        return jsonify({"error": "Stripe: STRIPE_SECRET_KEY no configurada. Agregala en Render Environment."}), 500

    try:
        session = _stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": PRICE_USD * 100,  # centavos
                    "product_data": {"name": "Web Analyzer PRO — Acceso Vitalicio"},
                },
                "quantity": 1,
            }],
            metadata={"user_id": str(g.current_user["id"])},
            success_url=request.host_url.rstrip("/") + "/checkout-success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url.rstrip("/") + "/",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        log.exception("Error creando sesión Stripe")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stripe-webhook", methods=["POST"])
def api_stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        log.warning("STRIPE_WEBHOOK_SECRET no configurada — webhook ignorado")
        return jsonify({"error": "Webhook no configurado"}), 400

    try:
        event = _stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, _stripe.error.SignatureVerificationError) as e:
        log.warning(f"Webhook inválido: {e}")
        return jsonify({"error": "Firma inválida"}), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        if user_id:
            upgrade_to_paid(int(user_id))
            track_event("user_upgraded", int(user_id))
            log.info(f"Usuario {user_id} actualizado a pago vía Stripe")

    return jsonify({"status": "ok"})


@app.route("/checkout-success")
def checkout_success():
    session_id = request.args.get("session_id", "")
    upgraded = False
    if session_id and _stripe and STRIPE_SECRET:
        try:
            sess = _stripe.checkout.Session.retrieve(session_id)
            if sess.get("payment_status") == "paid":
                user_id = sess.get("metadata", {}).get("user_id")
                if user_id:
                    upgrade_to_paid(int(user_id))
                    track_event("user_upgraded", int(user_id))
                    log.info(f"Usuario {user_id} actualizado a PRO (success page)")
                    upgraded = True
        except Exception as e:
            log.warning(f"Error verificando sesión en success: {e}")
    return render_template("checkout-success.html", session_id=session_id, upgraded=upgraded)


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

    # Generar URL compartible
    report_hash = hashlib.sha256(f"{url}-{time.time()}".encode()).hexdigest()[:12]
    create_shared_report(report_hash, url, {
        k: {"puntaje": s, "color": _color(s), "detalles": d}
        for k, (s, d) in scores.items()
    }, promedio)

    # Analytics
    user_id = g.current_user["id"] if g.current_user else None
    if user_id:
        increment_analyses(user_id)
        # Actualizar monitoreo si existe
        update_monitored_score(url, user_id, promedio)
    track_event("analysis_completed", user_id, url, json.dumps({"promedio": promedio}))

    # Determinar qué soluciones devolver según tier
    user_tier = g.current_user["tier"] if g.current_user else "free"
    soluciones = resultado.get("soluciones", [])

    if user_tier == "free":
        # Sin descarga — solo metadata de soluciones
        soluciones_out = [
            {"nombre": s["nombre"], "tipo": s["tipo"], "descripcion": s["descripcion"], "bloqueado": s["tipo"] in ("zip", "json")}
            for s in soluciones
        ]
    else:
        soluciones_out = [
            {"nombre": s["nombre"], "tipo": s["tipo"], "descripcion": s["descripcion"], "path": s.get("path", ""), "bloqueado": False}
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

    # Verificar tier
    if not g.current_user or g.current_user.get("tier") != "paid":
        return jsonify({
            "error": "Descarga exclusiva del plan pago",
            "action": "upgrade",
            "upgrade_url": "/api/upgrade",
        }), 402

    safe = os.path.basename(filename)
    path = (OUTPUT_DIR / safe).resolve()

    if not str(path).startswith(str(OUTPUT_DIR.resolve())):
        return jsonify({"error": "Acceso denegado"}), 403

    if not path.exists():
        return jsonify({"error": "Archivo no encontrado"}), 404

    user_id = g.current_user["id"] if g.current_user else None
    if user_id:
        increment_downloads(user_id)
    track_event("plugin_downloaded", user_id, filename)

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


@app.route("/api/stats")
def api_stats():
    from database import get_public_stats
    return jsonify(get_public_stats())


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
