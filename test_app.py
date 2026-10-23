"""
Tests de integración para la API Flask (app.py).
"""
import sys
import json
import pytest
from flask import g
from unittest.mock import patch, Mock, MagicMock

# ---------------------------------------------------------------------------
# Patch analyzer ANTES de importar app, y restaurarlo al finalizar la sesión
# ---------------------------------------------------------------------------
_analyzer_mock = MagicMock()
_analyzer_mock.listar_analisis.return_value = []


@pytest.fixture(scope="module", autouse=True)
def _patch_analyzer_module():
    """Inyecta el mock de 'analyzer' sólo durante esta sesión de tests."""
    original = sys.modules.get("analyzer")
    sys.modules["analyzer"] = _analyzer_mock
    # Importamos app aquí para que use el mock
    import importlib
    import app as _app_module  # noqa: F401 – side-effect: registra rutas
    yield
    if original is None:
        sys.modules.pop("analyzer", None)
    else:
        sys.modules["analyzer"] = original


from app import app  # noqa: E402 – importación después del patch


@pytest.fixture
def client():
    app.config["TESTING"] = True
    import app as app_module
    _original_dev = getattr(app_module, "DEV_MODE", False)
    app_module.DEV_MODE = True
    with app.test_client() as c:
        yield c
    app_module.DEV_MODE = _original_dev


# =============================================================================
# Health Check
# =============================================================================


class TestHealth:
    def test_health_returns_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_webapp_sets_transport_and_browser_security_headers(self, client):
        response = client.get("/")

        assert response.headers["Strict-Transport-Security"] == "max-age=31536000"
        assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "frame-ancestors 'self'" in response.headers["Content-Security-Policy"]


# =============================================================================
# Input Validation
# =============================================================================


class TestAnalyzeEndpoint:
    def test_requires_url(self, client):
        resp = client.post("/api/analyze", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    def test_accepts_valid_url(self, client):
        with patch("app.analizar") as mock_analizar, patch("app.create_shared_report") as mock_share, patch("app.track_event"):
            mock_analizar.return_value = {
                "url": "https://example.com",
                "url_final": "https://example.com",
                "fecha": "2026-05-10 00:00",
                "scorecard": {
                    "Rendimiento": (10, []),
                    "Accesibilidad": (10, []),
                    "SEO": (10, []),
                    "UX": (10, []),
                    "Conversión": (10, []),
                },
                "versiones": {"motor": "webanalyzer-engine-test", "perfil_seguridad": None},
                "psi": {
                    "performance_score": 8.2,
                    "lcp": "2.3 s",
                    "datos_campo_url": {
                        "nivel": "AVERAGE",
                        "metricas": {"LARGEST_CONTENTFUL_PAINT_MS": {"p75": 2300, "nivel": "AVERAGE"}},
                    },
                },
                "auditorias_rendimiento": [{
                    "id": "modern-image-formats",
                    "titulo": "Usar formatos de imagen modernos",
                    "estado": "issue",
                    "descripcion": "Se pueden reducir los bytes transferidos.",
                    "valor": "Ahorro potencial 20 KiB",
                }],
                "cobertura_practicas": [{
                    "id": 1,
                    "nombre": "Optimización de imágenes",
                    "estado": "medido_con_hallazgos",
                    "evidencia": "Lighthouse detectó formatos mejorables.",
                    "requiere": "PageSpeed Insights.",
                }],
                "cobertura_practicas_resumen": {
                    "controles_sitio": 19,
                    "medidos_directamente": 10,
                    "indicios": 2,
                    "requieren_navegador": 3,
                    "requieren_servidor": 4,
                },
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
            resp = client.post("/api/analyze", json={"url": "example.com"})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data["promedio"] == 10.0
            assert data["versiones"]["motor"] == "webanalyzer-engine-test"
            saved_scorecard = mock_share.call_args.args[2]
            assert saved_scorecard["_meta"]["motor"] == "webanalyzer-engine-test"
            assert saved_scorecard["_meta"]["perfil_seguridad"] is None
            assert saved_scorecard["_meta"]["seguridad"]["enabled"] is False
            assert saved_scorecard["_meta"]["rendimiento"]["puntaje_lighthouse"] == 8.2
            assert saved_scorecard["_meta"]["rendimiento"]["auditorias"][0]["id"] == "modern-image-formats"
            assert saved_scorecard["_meta"]["cobertura_practicas"][0]["id"] == 1
            assert saved_scorecard["_meta"]["resumen_cobertura_practicas"]["medidos_directamente"] == 10

    def test_analysis_rate_limit_uses_account_for_authenticated_users(self, client, monkeypatch):
        import app as app_module

        with app.test_request_context("/api/analyze", environ_base={"REMOTE_ADDR": "203.0.113.4"}):
            g.current_user = {"id": 42}
            assert app_module._analysis_rate_limit_key() == "user:42"

        with app.test_request_context("/api/analyze", environ_base={"REMOTE_ADDR": "203.0.113.4"}):
            g.current_user = None
            assert app_module._analysis_rate_limit_key() == "203.0.113.4"

        monkeypatch.delenv("TRUST_X_FORWARDED_FOR", raising=False)
        with app.test_request_context(
            "/api/analyze",
            headers={"X-Forwarded-For": "198.51.100.23, 10.0.0.5"},
            environ_base={"REMOTE_ADDR": "10.0.0.5"},
        ):
            g.current_user = None
            assert app_module._analysis_rate_limit_key() == "10.0.0.5"

        monkeypatch.setenv("TRUST_X_FORWARDED_FOR", "true")
        with app.test_request_context(
            "/api/analyze",
            headers={"X-Forwarded-For": "198.51.100.23, 10.0.0.5"},
            environ_base={"REMOTE_ADDR": "10.0.0.5"},
        ):
            g.current_user = None
            assert app_module._analysis_rate_limit_key() == "198.51.100.23"

        with app.test_request_context(
            "/api/analyze",
            headers={"X-Forwarded-For": "not-an-ip"},
            environ_base={"REMOTE_ADDR": "203.0.113.4"},
        ):
            g.current_user = None
            assert app_module._analysis_rate_limit_key() == "203.0.113.4"

    def test_shared_report_keeps_engine_version_out_of_scorecard_rows(self, client):
        import app as app_module

        report = {
            "id": "report123",
            "url": "https://example.test/",
            "scorecard": {
                "SEO": {"puntaje": 9, "color": "verde", "detalles": []},
                "_meta": {
                    "motor": "webanalyzer-engine-2.0.0",
                    "perfil_seguridad": "argon-security-controls-v2",
                    "seguridad": {
                        "enabled": True,
                        "metodologia": "Índice Argon de seguridad web",
                        "puntaje": 10,
                        "catalogo_version": "argon-security-controls-v2",
                        "resumen": {
                            "evaluados": 7,
                            "catalogo_total": 22,
                            "cobertura_porcentaje": 32,
                            "aprobados": 7,
                            "observaciones": 0,
                            "no_evaluados": 12,
                            "no_aplica": 3,
                        },
                    },
                },
            },
            "promedio": 9,
            "created_at": "2026-10-22",
            "views": 1,
        }
        with patch.object(app_module, "get_shared_report", return_value=report):
            response = client.get("/r/report123")

        assert response.status_code == 200
        assert b"webanalyzer-engine-2.0.0" in response.data
        assert b"Cobertura 7/22 controles" in response.data
        assert b"32%" in response.data
        assert b"argon-security-controls-v2" in response.data
        assert "_meta" not in report["scorecard"]

    def test_shared_report_renders_performance_coverage_and_security_evidence(self, client):
        import app as app_module

        report = {
            "id": "report456",
            "url": "https://example.test/",
            "scorecard": {
                "_meta": {
                    "motor": "webanalyzer-engine-2.0.0",
                    "perfil_seguridad": "argon-security-controls-v2",
                    "rendimiento": {
                        "puntaje_lighthouse": 8.2,
                        "datos_campo_url": {
                            "nivel": "AVERAGE",
                            "metricas": {"LARGEST_CONTENTFUL_PAINT_MS": {"p75": 2300, "nivel": "AVERAGE"}},
                        },
                        "auditorias": [{
                            "id": "modern-image-formats",
                            "titulo": "Usar formatos de imagen modernos",
                            "estado": "issue",
                            "descripcion": "Se pueden reducir los bytes transferidos.",
                            "valor": "Ahorro potencial 20 KiB",
                        }],
                    },
                    "cobertura_practicas": [{
                        "id": 1,
                        "nombre": "Optimización de imágenes",
                        "estado": "medido_con_hallazgos",
                        "evidencia": "Lighthouse detectó formatos mejorables.",
                        "requiere": "PageSpeed Insights.",
                    }],
                    "resumen_cobertura_practicas": {
                        "controles_sitio": 19,
                        "medidos_directamente": 10,
                        "indicios": 2,
                        "requieren_navegador": 3,
                        "requieren_servidor": 4,
                    },
                    "seguridad": {
                        "enabled": True,
                        "metodologia": "Índice Argon de seguridad web, basado en metodología Argon Defender",
                        "puntaje": 8.5,
                        "catalogo_version": "argon-security-controls-v2",
                        "resumen": {
                            "evaluados": 7,
                            "catalogo_total": 22,
                            "cobertura_porcentaje": 32,
                            "aprobados": 6,
                            "observaciones": 1,
                            "no_evaluados": 12,
                            "no_aplica": 3,
                        },
                        "controles": [{
                            "id": "header-csp",
                            "titulo": "Content Security Policy",
                            "estado": "issue",
                            "gravedad": "alta",
                            "evidencia": "No se observó Content-Security-Policy.",
                            "recomendacion": "Definir una CSP ajustada a los recursos reales.",
                        }],
                        "limites": ["Evaluación pasiva de la respuesta y las cabeceras visibles."],
                    },
                },
            },
            "promedio": 8.8,
            "created_at": "2026-10-22",
            "views": 1,
        }
        with patch.object(app_module, "get_shared_report", return_value=report):
            response = client.get("/r/report456")

        assert response.status_code == 200
        assert b"Lighthouse m\xc3\xb3vil: <strong>8.2/10</strong>" in response.data
        assert b"LARGEST_CONTENTFUL_PAINT_MS p75 2300" in response.data
        assert b"Usar formatos de imagen modernos" in response.data
        assert b"Cobertura de las 20 pr\xc3\xa1cticas de rendimiento" in response.data
        assert b"Lighthouse detect\xc3\xb3 formatos mejorables." in response.data
        assert b"Content Security Policy" in response.data
        assert b"No se observ\xc3\xb3 Content-Security-Policy." in response.data
        assert b"Definir una CSP ajustada a los recursos reales." in response.data


# =============================================================================
# Download / Path Traversal
# =============================================================================


class TestDownload:
    def test_rejects_invalid_chars(self, client):
        resp = client.get("/api/download/../../etc/passwd")
        assert resp.status_code in (400, 404)

    def test_rejects_null_byte(self, client):
        resp = client.get("/api/download/test%00.exe")
        assert resp.status_code in (400, 404)

    def test_not_found_for_missing_file(self, client):
        resp = client.get("/api/download/no-existe-12345.zip")
        assert resp.status_code == 404


# =============================================================================
# History
# =============================================================================


class TestHistory:
    def test_returns_list(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


# =============================================================================
# Index
# =============================================================================


class TestIndex:
    def test_index_loads(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"WebAnalyzer" in resp.data or b"Web Analyzer" in resp.data
