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
