"""
Tests QA críticos — API Flask app.py (7 de los 25 prioritarios).

Cobertura (casos de la matriz de 200):
  AP1 E10/E11  /api/lead sin validación de email (open relay)  Crítico
  AP2 E10      /api/lead sin rate limit estricto ............. Crítico
  AP3 E5/D9    /api/history global (fuga de URLs ajenas) ..... Crítico
  AP4 E12/D8   report_hash determinístico (enumerable) ....... Alto
  AP5 E13/D28  user_token aceptado en query string ........... Alto
  AP6 E33      Excepciones filtran detalle interno ........... Medio
  AP8 C31/E8   depth sin clamp (crawl masivo / DoS) .......... Alto
"""
import pytest
from unittest.mock import patch


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


def _resultado():
    return {
        "url": "https://s.com",
        "url_final": "https://s.com",
        "fecha": "2026-08-13 12:00",
        "scorecard": {k: (10, []) for k in ("Rendimiento", "Accesibilidad", "SEO", "UX", "Conversión")},
        "tecnologia": [],
        "meta": {},
        "imagenes": {},
        "headings": {},
        "forms": {},
        "scripts": {},
        "size_kb": 100,
        "hallazgos": [],
        "recomendaciones": [],
        "soluciones": [],
        "errores": [],
    }


# ---------------------------------------------------------------------------
# AP1 (E10/E11) — /api/lead debe validar el email y rechazar inyección CRLF
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("email", [
    "no-es-un-mail",
    "a@b.com\r\nBcc: x@y.com",
    "a@b.com\nTo: spam@x.com",
    "a@b.com\r\nX-Injected: 1",
])
def test_ap1_lead_valida_email_y_rechaza_inyeccion(client, email):
    mod = client.app_module
    with patch.object(mod, "send_email", return_value=True), \
         patch.object(mod, "track_event"):
        resp = client.post("/api/lead", json={"email": email, "url": "https://s.com"})
    assert resp.status_code == 400, (
        f"email inválido/inyectado aceptado: {email!r} — el servidor se usa "
        "como relay de spam"
    )


# ---------------------------------------------------------------------------
# AP2 (E10) — /api/lead debe tener rate limit estricto (anti spam de emails)
# ---------------------------------------------------------------------------
def test_ap2_lead_tiene_rate_limit_estricto(client):
    mod = client.app_module
    with patch.object(mod, "send_email", return_value=True), \
         patch.object(mod, "track_event"):
        codes = [
            client.post("/api/lead", json={"email": f"u{i}@x.com", "url": "https://s.com"}).status_code
            for i in range(5)
        ]
    assert 429 in codes, (
        f"permite {len(codes)} envíos de email seguidos sin limitar: {codes} "
        "(30/min por IP es demasiado para un endpoint que envía emails)"
    )


# ---------------------------------------------------------------------------
# AP3 (E5/D9) — /api/history debe filtrar por usuario (no ser global)
# ---------------------------------------------------------------------------
def test_ap3_history_filtra_por_usuario(client):
    mod = client.app_module
    entries = [
        {"url": "https://a.com", "user_id": 1},
        {"url": "https://b.com", "user_id": 2},
    ]
    with patch.object(mod, "listar_analisis", return_value=entries), \
         patch.object(mod, "get_user_by_token", return_value={"id": 1, "email": "a@x.com", "tier": "free"}):
        resp = client.get("/api/history", headers={"X-User-Token": "tok-a"})
    assert resp.status_code == 200
    urls = [e["url"] for e in resp.get_json()]
    assert urls == ["https://a.com"], (
        "el historial es global: un usuario ve las URLs que auditaron otros"
    )


# ---------------------------------------------------------------------------
# AP4 (E12/D8) — report_hash debe ser aleatorio (no sha256(url) adivinable)
# ---------------------------------------------------------------------------
def test_ap4_report_hash_es_aleatorio(client):
    mod = client.app_module
    with patch.object(mod, "analizar", return_value=_resultado()), \
         patch.object(mod, "create_shared_report"), \
         patch.object(mod, "track_event"):
        r1 = client.post("/api/analyze", json={"url": "https://s.com"}).get_json()
        r2 = client.post("/api/analyze", json={"url": "https://s.com"}).get_json()
    assert r1["report_hash"] != r2["report_hash"], (
        "report_hash = sha256(url)[:12]: los reportes compartidos son "
        "adivinables/enumerables para cualquier sitio"
    )


# ---------------------------------------------------------------------------
# AP5 (E13/D28) — user_token solo por header, nunca en query string
# ---------------------------------------------------------------------------
def test_ap5_user_token_no_se_acepta_en_query(client):
    mod = client.app_module
    mod.DEV_MODE = False
    try:
        with patch.object(mod, "get_user_by_token") as m:
            m.return_value = {"id": 1, "email": "a@x.com", "tier": "free"}
            resp = client.get("/api/download/algo.zip?user_token=abc123")
        assert resp.status_code == 401
        m.assert_not_called()  # el token en query no debe autenticar
    finally:
        mod.DEV_MODE = True


# ---------------------------------------------------------------------------
# AP6 (E33) — los errores internos no deben filtrar el detalle de la excepción
# ---------------------------------------------------------------------------
def test_ap6_register_no_filtra_detalle_interno(client):
    mod = client.app_module
    with patch.object(mod, "create_user", side_effect=RuntimeError(r"db path C:\secret\data.db")):
        resp = client.post("/api/auth/register", json={"email": "a@x.com", "password": "123456"})
    assert resp.status_code == 500
    assert "secret" not in resp.get_json().get("error", ""), (
        "el mensaje de la excepción interna se devuelve al cliente"
    )


# ---------------------------------------------------------------------------
# AP8 (C31/E8) — depth debe clampearse (crawl masivo / DoS del operador)
# ---------------------------------------------------------------------------
def test_ap8_analyze_clampea_depth(client):
    mod = client.app_module
    with patch.object(mod, "_analizar_multipagina", return_value=_resultado()) as multi, \
         patch.object(mod, "analizar", return_value=_resultado()), \
         patch.object(mod, "create_shared_report"), \
         patch.object(mod, "track_event"):
        client.post("/api/analyze", json={"url": "https://s.com", "depth": 999})
    assert multi.call_args[0][1] <= 5, (
        "depth sin límite: un atacante crawlea cientos de páginas internas "
        "(agota quota, CPU y disco del operador)"
    )
