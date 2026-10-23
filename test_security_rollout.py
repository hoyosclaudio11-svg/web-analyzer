from requests.structures import CaseInsensitiveDict
from unittest.mock import Mock

import analyzer


def _analyze_with_flag(monkeypatch, enabled):
    response = Mock(
        url="https://example.test/",
        text="<html><head><title>Example</title><meta name='viewport' content='width=device-width'></head><body><h1>Example</h1></body></html>",
        headers=CaseInsensitiveDict({
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=()",
        }),
        raw=Mock(headers=None),
    )
    monkeypatch.setattr(analyzer, "_safe_get", lambda url: response)
    monkeypatch.setattr(analyzer, "_fetch_pagespeed_insights", lambda url: None)
    monkeypatch.setattr(analyzer, "_generar_soluciones", lambda *args: [])
    monkeypatch.setattr(analyzer, "_guardar_analisis", lambda *args: None)
    monkeypatch.setenv("ARGON_SECURITY_ENABLED", "true" if enabled else "false")

    return analyzer.analizar("https://example.test/")


def test_security_is_disabled_and_does_not_change_existing_scorecard_by_default(monkeypatch):
    result = _analyze_with_flag(monkeypatch, enabled=False)

    assert result["seguridad"]["enabled"] is False
    assert "Seguridad" not in result["scorecard"]
    assert result["versiones"]["perfil_seguridad"] is None


def test_enabled_security_score_records_profile_and_control_coverage(monkeypatch):
    result = _analyze_with_flag(monkeypatch, enabled=True)

    assert result["seguridad"]["enabled"] is True
    assert result["seguridad"]["resumen"]["evaluados"] == 7
    assert result["seguridad"]["resumen"]["catalogo_total"] == 22
    assert "Seguridad" in result["scorecard"]
    assert result["versiones"]["motor"] == analyzer.ENGINE_VERSION
    assert result["versiones"]["perfil_seguridad"] == result["seguridad"]["catalogo_version"]


def test_pagespeed_parser_exposes_selected_lighthouse_and_field_metrics(monkeypatch):
    payload = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.82}},
            "audits": {
                "modern-image-formats": {
                    "title": "Serve images in modern formats",
                    "description": "Convert images to WebP.",
                    "score": 0.5,
                    "scoreDisplayMode": "numeric",
                    "displayValue": "Potential savings 20 KiB",
                },
                "render-blocking-resources": {
                    "title": "Eliminate render-blocking resources",
                    "score": 1,
                    "scoreDisplayMode": "binary",
                },
                "interaction-to-next-paint": {
                    "title": "Interaction to Next Paint",
                    "score": None,
                    "scoreDisplayMode": "notApplicable",
                },
            },
        },
        "loadingExperience": {
            "overall_category": "AVERAGE",
            "metrics": {
                "LARGEST_CONTENTFUL_PAINT_MS": {"percentile": 2300, "category": "AVERAGE"},
            },
        },
        "originLoadingExperience": {},
    }
    captured = {}

    def fake_get(url, timeout, headers):
        captured.update({"url": url, "timeout": timeout, "headers": headers})
        return Mock(status_code=200, json=lambda: payload)

    monkeypatch.setattr(analyzer.requests, "get", fake_get)

    result = analyzer._fetch_pagespeed_insights("https://example.test/")

    assert result["performance_score"] == 8.2
    audits = {audit["id"]: audit for audit in result["auditorias"]}
    assert audits["modern-image-formats"]["estado"] == "issue"
    assert audits["render-blocking-resources"]["estado"] == "pass"
    assert audits["interaction-to-next-paint"]["estado"] == "not_applicable"
    assert result["datos_campo_url"]["metricas"]["LARGEST_CONTENTFUL_PAINT_MS"]["p75"] == 2300
    assert captured["timeout"] == 20
    assert "WebAnalyzer/" in captured["headers"]["User-Agent"]
