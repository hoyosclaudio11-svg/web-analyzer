"""
Tests unitarios para el motor de análisis (analyzer.py).
"""
import sys
import json
import pytest
from unittest.mock import patch, Mock

from analyzer import (
    _is_public_url,
    _evaluar_seo,
    _evaluar_rendimiento,
    _evaluar_accesibilidad,
    _evaluar_conversion,
    _evaluar_ux,
    _generar_plugin_wordpress,
    _extraer_metadatos,
    _extraer_imagenes,
    _extraer_headings,
    _extraer_forms,
    _score_color,
    analizar,
)

# =============================================================================
# SSRF Protection
# =============================================================================


class TestSSRF:
    def test_blocks_localhost(self):
        ok, reason = _is_public_url("http://localhost:5100/api")
        assert not ok
        assert "interno" in reason.lower()

    def test_blocks_127_0_0_1(self):
        ok, reason = _is_public_url("http://127.0.0.1/test")
        assert not ok

    def test_blocks_file_protocol(self):
        ok, reason = _is_public_url("file:///etc/passwd")
        assert not ok

    def test_allows_public_url(self):
        ok, reason = _is_public_url("https://www.google.com")
        assert ok

    def test_blocks_aws_metadata(self):
        """169.254.169.254 es link-local — debe ser bloqueado."""
        ok, reason = _is_public_url("http://169.254.169.254/latest/meta-data/")
        assert not ok

    def test_blocks_0_0_0_0(self):
        ok, reason = _is_public_url("http://0.0.0.0:8080/")
        assert not ok


# =============================================================================
# Evaluadores
# =============================================================================


class TestSEO:
    def _meta_fixture(self, **overrides):
        """Meta completo con valores por defecto."""
        base = {
            "title": "Título del sitio — 50 caracteres bien medidos",
            "title_length": 50,
            "description": "Descripción del sitio de 120 caracteres con keyword principal y llamado a la acción para atraer tráfico",
            "description_length": 100,
            "viewport": "width=device-width",
            "robots": "index,follow",
            "canonical": "https://example.com",
            "og_title": "OG Title",
            "og_description": "OG Desc",
            "og_image": "https://example.com/img.jpg",
            "og_url": "https://example.com",
            "og_type": "website",
            "og_site_name": "Example",
            "og_locale": "es_AR",
            "twitter_card": "summary_large_image",
            "twitter_title": "Twitter Title",
            "twitter_description": "Twitter Desc",
            "twitter_image": "https://example.com/img.jpg",
            "generator": "WordPress",
        }
        base.update(overrides)
        return base

    def test_perfect_score(self):
        meta = self._meta_fixture()
        headings = {"h1": {"count": 1, "texts": ["Título"]}}
        score, detalles = _evaluar_seo(meta, headings, None)
        assert score == 10

    def test_no_title(self):
        meta = self._meta_fixture(title=None, title_length=0)
        headings = {"h1": {"count": 0, "texts": []}}
        score, detalles = _evaluar_seo(meta, headings, None)
        assert score <= 5  # Penalización fuerte por falta de title + sin H1

    def test_short_title(self):
        meta = self._meta_fixture(title="Corto", title_length=5)
        headings = {"h1": {"count": 1, "texts": ["Corto"]}}
        score, detalles = _evaluar_seo(meta, headings, None)
        assert score < 10  # Penalización por title corto


class TestRendimiento:
    def test_perfect(self):
        imgs = {"total": 10, "sin_lazy": 0, "formatos": ["webp"]}
        scripts = {"bloqueantes": 0}
        score, detalles = _evaluar_rendimiento(imgs, scripts, 50)
        assert score == 10

    def test_all_no_lazy(self):
        imgs = {"total": 10, "sin_lazy": 10, "formatos": ["jpg"]}
        scripts = {"bloqueantes": 0}
        score, detalles = _evaluar_rendimiento(imgs, scripts, 50)
        assert score < 10  # Penalización por zero lazy loading

    def test_heavy_page(self):
        imgs = {"total": 0, "sin_lazy": 0, "formatos": []}
        scripts = {"bloqueantes": 0}
        score, detalles = _evaluar_rendimiento(imgs, scripts, 600)
        assert score < 10  # Penalización por página pesada


class TestAccesibilidad:
    def test_missing_h1(self):
        imgs = {"sin_alt": 0}
        headings = {"h1": {"count": 0}, "jerarquia_ok": True}
        forms = {"lista": []}
        soup = Mock()
        soup.find.return_value = None
        soup.find_all.return_value = []
        score, detalles = _evaluar_accesibilidad(imgs, headings, forms, soup)
        assert score < 10  # Penalización por falta de H1

    def test_images_without_alt(self):
        imgs = {"sin_alt": 5}
        headings = {"h1": {"count": 1}, "jerarquia_ok": True}
        forms = {"lista": []}
        soup = Mock()
        soup.find.return_value = None
        soup.find_all.return_value = []
        score, detalles = _evaluar_accesibilidad(imgs, headings, forms, soup)
        assert score < 10


# =============================================================================
# Plugin Generation
# =============================================================================


class TestPluginGeneration:
    def test_generates_valid_php_structure(self):
        resultado = {
            "meta": {"title": "Mi Sitio", "og_site_name": "Mi Sitio", "description": "Descripción"},
            "url": "https://mi-sitio.com.ar",
        }
        code = _generar_plugin_wordpress(resultado, "mi_sitio_com_ar")
        assert "<?php" in code
        assert "Plugin Name:" in code
        # Sin guiones en nombres de función
        assert "mi_sitio_com_ar_build_meta_desc" in code

    def test_safe_domain_handles_special_chars(self):
        resultado = {
            "meta": {"title": "Test & Demo", "og_site_name": None, "description": ""},
            "url": "https://test-site.org",
        }
        code = _generar_plugin_wordpress(resultado, "test_site_org")
        assert "test_site_org_newsletter_shortcode" in code


# =============================================================================
# Color helper
# =============================================================================


def test_score_color():
    assert _score_color(9) == "verde"
    assert _score_color(8) == "verde"
    assert _score_color(7) == "amarillo"
    assert _score_color(5) == "amarillo"
    assert _score_color(4) == "rojo"
    assert _score_color(0) == "rojo"
