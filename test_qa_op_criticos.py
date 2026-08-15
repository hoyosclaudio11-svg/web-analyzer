"""
Tests QA — OPERACIÓN y RETENCIÓN DE DATOS (fila 1-3 de la siguiente tanda).

Cobertura (casos de la matriz de 200, ver docs/QA-siguientes-priorizados.md):
  D5  Email de lead con link roto (/report/ vs /r/) ......... Crítico
  E9  Disk fill: _guardar_analisis sin purga/TTL ............ Alto
  D10 Datos de 3ros sin consentimiento: valores de inputs ... Alto
"""
import json
import os
import time

import pytest
from unittest.mock import patch

import analyzer


@pytest.fixture
def client():
    import app as app_module
    app_module.DEV_MODE = True
    app_module.API_KEY = ""
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        c.app_module = app_module
        yield c
    app_module.DEV_MODE = False


def _resultado_minimo(url="https://s.com"):
    return {
        "url": url,
        "fecha": "2026-08-14 12:00",
        "scorecard": {},
        "meta": {},
        "imagenes": {},
        "headings": {},
        "forms": {},
        "scripts": {},
        "enlaces": {},
        "size_kb": 1,
        "hallazgos": [],
        "recomendaciones": [],
        "soluciones": [],
        "errores": [],
    }


# ---------------------------------------------------------------------------
# D5 — el email de lead debe apuntar a la ruta REAL del reporte (/r/, no /report/)
# ---------------------------------------------------------------------------
def test_d5_email_lead_usa_ruta_real_del_reporte(client):
    mod = client.app_module
    mod._LEAD_SENDS.clear()  # AP2 (rate limit) deja la cuota agotada en la misma corrida
    capturado = {}

    def fake_send(to, subject, body):
        capturado["body"] = body
        return True

    with patch.object(mod, "send_email", side_effect=fake_send), \
         patch.object(mod, "track_event"):
        resp = client.post("/api/lead", json={
            "email": "cliente@x.com",
            "url": "https://s.com",
            "report_hash": "abc123def456",
        })
    assert resp.status_code == 200
    assert "/r/abc123def456" in capturado["body"], (
        "el email apunta a /report/{hash}, ruta inexistente — el lead recibe "
        "un reporte inaccesible (BUG REAL D5)"
    )
    assert "/report/" not in capturado["body"], (
        "el email usa la ruta vieja /report/ en vez de /r/"
    )


# ---------------------------------------------------------------------------
# E9 — _guardar_analisis debe purgar por antigüedad (TTL) y tope por dominio
# ---------------------------------------------------------------------------
def test_e9_guardar_analisis_purga_por_antiguedad(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "_ANALISIS_DIR", str(tmp_path))
    viejo = tmp_path / "sitio_viejo_20260601_100000.json"
    viejo.write_text("{}", encoding="utf-8")
    viejo_ts = time.time() - 40 * 86400  # 40 días atrás
    os.utime(viejo, (viejo_ts, viejo_ts))

    analyzer._guardar_analisis(_resultado_minimo(url="https://nuevo.com"))

    assert not viejo.exists(), (
        "el análisis de hace 40 días no se purgó (TTL) — el disco se llena (E9)"
    )


def test_e9_tope_de_archivos_por_dominio(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "_ANALISIS_DIR", str(tmp_path))
    for i in range(25):
        (tmp_path / f"mismo_dom_20260814_{i:06d}.json").write_text("{}", encoding="utf-8")

    analyzer._purga_analisis()

    restantes = [f for f in tmp_path.iterdir() if f.suffix == ".json"]
    assert len(restantes) <= 20, (
        "más de 20 archivos por dominio: el análisis repetido llena el disco (E9)"
    )


# ---------------------------------------------------------------------------
# D10 — el JSON guardado no debe incluir valores de inputs/credenciales
# ---------------------------------------------------------------------------
def test_d10_json_guardado_excluye_valores_de_inputs(monkeypatch, tmp_path):
    monkeypatch.setattr(analyzer, "_ANALISIS_DIR", str(tmp_path))
    resultado = _resultado_minimo()
    resultado["forms"] = {
        "total": 1,
        "con_email": 1,
        "lista": [{
            "action": "/procesar",
            "method": "POST",
            "inputs": 2,
            "labels": 1,
            "has_submit": True,
            "has_email": True,
            "valores": [
                {"name": "email", "value": "cliente@x.com"},
                {"name": "password", "value": "secreto123"},
            ],
        }],
    }
    analyzer._guardar_analisis(resultado)

    archivos = [f for f in tmp_path.iterdir() if f.suffix == ".json"]
    assert len(archivos) == 1
    serializado = json.dumps(json.loads(archivos[0].read_text(encoding="utf-8")))
    assert "secreto123" not in serializado, (
        "el JSON del análisis persiste valores de inputs (D10)"
    )
    assert "cliente@x.com" not in serializado, (
        "el JSON del análisis persiste el email del input (D10)"
    )


# ---------------------------------------------------------------------------
# D6 — el email de lead sin report_hash NO debe apuntar al sitio del cliente
# ---------------------------------------------------------------------------
def test_d6_email_lead_siempre_con_report_hash(client):
    mod = client.app_module
    mod._LEAD_SENDS.clear()  # AP2 deja la cuota del rate limit agotada
    body = {}

    def fake_send(to, subject, texto):
        body["texto"] = texto
        return True

    with patch.object(mod, "send_email", side_effect=fake_send), \
         patch.object(mod, "track_event"), \
         patch.object(mod, "create_shared_report", return_value="abc123") as csr:
        resp = client.post("/api/lead", json={"email": "u@x.com", "url": "https://cliente.com"})
    assert resp.status_code == 200
    assert "https://webanalyzer.com.ar/r/" in body["texto"], (
        "sin report_hash el email apunta al sitio del cliente en vez del "
        "reporte real (D6)"
    )
    assert csr.called, "no se generó un report_hash server-side (D6)"


# ---------------------------------------------------------------------------
# E13 — el token de sesión nunca debe aparecer en los logs
# ---------------------------------------------------------------------------
def test_e13_token_no_aparece_en_logs(client, caplog):
    token = "tok_secreto_abc123"
    with caplog.at_level("INFO", logger="web-analyzer"):
        client.get("/api/history", headers={"X-User-Token": token})
        client.get(f"/api/history?user_token={token}")
    assert token not in caplog.text, (
        "el X-User-Token se filtra a los logs de acceso (E13)"
    )


# ---------------------------------------------------------------------------
# E31 — log injection: CRLF en URL/path no debe crear líneas falsas
# ---------------------------------------------------------------------------
def test_e31_sanear_log_escapa_crlf():
    import app as app_module
    texto = "url=https://x.com/\nFAKE\n2026-01-01"
    saneado = app_module._sanear_log(texto)
    assert "\n" not in saneado, "CRLF sin escapar en el log (E31)"
    assert "\\nFAKE" in saneado


def test_e31_crlf_en_path_no_inyecta_lineas(client, caplog):
    with caplog.at_level("INFO", logger="web-analyzer"):
        client.get("/api/health%0D%0AEVIL=1")
    assert "\nEVIL" not in caplog.text, (
        "CRLF en el path del request inyecta líneas falsas al log (E31)"
    )
    assert "\\nEVIL" in caplog.text


def test_e31_crlf_en_url_no_inyecta_lineas(client, caplog):
    with patch.object(analyzer, "_safe_get", side_effect=ValueError("boom")), \
         caplog.at_level("INFO", logger="web-analyzer"):
        client.post("/api/analyze", json={"url": "https://x.com/\nFAKE"})
    assert "\nFAKE" not in caplog.text, (
        "CRLF en la URL del análisis inyecta líneas falsas al log (E31)"
    )


# ---------------------------------------------------------------------------
# E14 — logout debe revocar el token (un token robado no vale para siempre)
# ---------------------------------------------------------------------------
def test_e14_logout_revoca_el_token(client, tmp_path):
    import database as db_mod
    orig_path = db_mod.DB_PATH
    orig_local = getattr(db_mod._local, "db", None)
    db_mod.DB_PATH = tmp_path / "test.db"
    if hasattr(db_mod._local, "db"):
        del db_mod._local.db  # _conn usa hasattr, no truthiness
    try:
        db_mod.init_db()
        # Registro + login reales contra la DB temporal
        resp = client.post("/api/auth/register", json={"email": "u@x.com", "password": "pass1234"})
        assert resp.status_code == 201
        resp = client.post("/api/auth/login", json={"email": "u@x.com", "password": "pass1234"})
        token = resp.get_json()["token"]
        assert db_mod.get_user_by_token(token) is not None

        # Logout: el token deja de valer
        resp = client.post("/api/auth/logout", headers={"X-User-Token": token})
        assert resp.status_code == 200
        assert db_mod.get_user_by_token(token) is None, (
            "el token sigue válido después del logout (E14)"
        )
    finally:
        db_mod.DB_PATH = orig_path
        if orig_local is None:
            if hasattr(db_mod._local, "db"):
                del db_mod._local.db
        else:
            db_mod._local.db = orig_local


# ---------------------------------------------------------------------------
# E39 — credenciales SMTP hardcodeadas en el repo (robo de secretos)
# ---------------------------------------------------------------------------
def test_e39_smtp_pass_sin_fallback_hardcodeado():
    """E39 — SMTP_PASS no debe tener fallback con credencial real en el código."""
    import re
    import app as app_mod

    src = open(app_mod.__file__, encoding="utf-8").read()
    m = re.search(
        r'SMTP_PASS\s*=\s*os\.environ\.get\(\s*["\']SMTP_PASS["\']\s*,\s*["\']([^"\']*)["\']\s*\)',
        src,
    )
    assert m, "SMTP_PASS no usa os.environ.get con default"
    assert m.group(1) == "", (
        f"fallback de SMTP_PASS no vacío (credencial en el repo): {m.group(1)!r} (E39)"
    )
    assert "25YmQhbaWJ" not in src, (
        "la credencial que estaba commiteada sigue en el código (E39)"
    )


# ---------------------------------------------------------------------------
# E15 — lockout por cuenta tras N fallos (independiente de la IP)
# ---------------------------------------------------------------------------
def test_e15_lockout_por_cuenta_independiente_de_ip(client, tmp_path):
    """5 fallos de login bloquean la cuenta aunque la IP cambie (E15)."""
    mod = client.app_module
    mod._LOGIN_FAILS.clear()
    mod.limiter.reset()
    import database as db_mod

    orig_path = db_mod.DB_PATH
    orig_local = getattr(db_mod._local, "db", None)
    db_mod.DB_PATH = tmp_path / "test.db"
    if hasattr(db_mod._local, "db"):
        del db_mod._local.db
    try:
        db_mod.init_db()
        client.post("/api/auth/register", json={"email": "lock@x.com", "password": "pass1234"})
        for _ in range(5):
            r = client.post("/api/auth/login", json={"email": "lock@x.com", "password": "mala"})
            assert r.status_code == 401
        # 6to intento con la password CORRECTA -> la cuenta está bloqueada (429)
        r = client.post("/api/auth/login", json={"email": "lock@x.com", "password": "pass1234"})
        assert r.status_code == 429, (
            "la cuenta no se bloquea tras 5 fallos aunque la password sea correcta (E15)"
        )
        assert (r.get_json() or {}).get("code") == "ACCOUNT_LOCKED"
    finally:
        mod._LOGIN_FAILS.clear()
        db_mod.DB_PATH = orig_path
        if orig_local is None:
            if hasattr(db_mod._local, "db"):
                del db_mod._local.db
        else:
            db_mod._local.db = orig_local
