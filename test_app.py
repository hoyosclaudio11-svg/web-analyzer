"""
Tests de integración para la API Flask (app.py).
"""
import sys
import json
import pytest
from unittest.mock import patch, Mock, MagicMock

# ---------------------------------------------------------------------------
# Patch analyzer ANTES de importar app, y restaurarlo al finalizar la sesión
# ---------------------------------------------------------------------------
_analyzer_mock = MagicMock()
_analyzer_mock.listar_analisis.return_value = []


@pytest.fixture(scope="session", autouse=True)
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
        with patch("app.analizar") as mock_analizar:
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
