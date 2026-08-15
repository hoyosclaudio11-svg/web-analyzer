"""
Tests QA críticos — MOTOR DE ANÁLISIS analyzer.py (8 de los 25 prioritarios).

Cobertura (casos de la matriz de 200):
  A1  E2        SSRF: representaciones alternas de IP ......... Alto
  A2  E1        SSRF: DNS rebinding (no re-resolver) .......... Crítico
  A3  E7        Respuesta sin límite de tamaño (gzip bomb) .... Crítico
  A4  C16/A4    SPA renderizado en cliente se puntúa basura ... Crítico
  A5  C8        alt="" decorativo se cuenta como sin-alt ...... Alto
  A6  C4        Descripción en JSON-LD ignorada ............... Alto
  A7  C11       Forms con aria-label penalizados .............. Alto
  A9  E26       URL sin encode en PageSpeed Insights .......... Alto
"""
import re
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from bs4 import BeautifulSoup

import analyzer

from analyzer import (
    _evaluar_accesibilidad,
    _evaluar_seo,
    _extraer_forms,
    _extraer_headings,
    _extraer_imagenes,
    _extraer_metadatos,
    _fetch_pagespeed_insights,
    _generar_soluciones,
    _is_public_url,
    _safe_get,
    analizar,
)


# ---------------------------------------------------------------------------
# A1 (E2) — SSRF: representaciones alternas de direcciones internas
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("url", [
    "http://[::ffff:127.0.0.1]/",   # IPv4 mapeada a IPv6
    "http://[::1]/",                # loopback IPv6
    "http://127.1/",                # 127.0.0.1 abreviado
    "http://2130706433/",           # 127.0.0.1 en decimal
    "http://0x7f000001/",           # 127.0.0.1 en hex
])
def test_a1_ssrf_bloquea_representaciones_alternas(url):
    ok, reason = _is_public_url(url)
    assert not ok, f"URL interna no bloqueada: {url}"


# ---------------------------------------------------------------------------
# A2 (E1) — SSRF por DNS rebinding: pin de IP (no re-resolver)
# ---------------------------------------------------------------------------
def test_a2_ssrf_pina_la_ip_validada_y_no_re_resuelve():
    with patch("analyzer.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("1.2.3.4", 80))]), \
         patch("analyzer.requests.Session") as Sess:
        sess = Sess.return_value
        resp = Mock()
        resp.is_redirect = False
        resp.raise_for_status = Mock()
        sess.get.return_value = resp
        _safe_get("http://example.com/")
        called_host = urlparse(sess.get.call_args[0][0]).hostname
    # La conexión real debe ir a la IP ya validada (TOCTOU / rebinding).
    assert called_host == "1.2.3.4"


# ---------------------------------------------------------------------------
# A3 (E7) — límite de tamaño de respuesta (gzip bomb / página gigante)
# ---------------------------------------------------------------------------
def test_a3_safe_get_rechaza_respuestas_gigantes():
    with patch("analyzer.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("1.2.3.4", 80))]), \
         patch("analyzer.requests.Session") as Sess:
        sess = Sess.return_value
        resp = Mock()
        resp.is_redirect = False
        resp.raise_for_status = Mock()
        resp.headers = {"Content-Length": "999999999"}
        sess.get.return_value = resp
        with pytest.raises(ValueError):
            _safe_get("http://example.com/")


# ---------------------------------------------------------------------------
# A4 (C16) — SPA renderizado en cliente: detectar y no puntuar HTML vacío
# ---------------------------------------------------------------------------
def test_a4_spa_se_detecta_y_no_se_puntua_html_vacio():
    html = '<html><head><title>SPA</title></head><body><div id="root"></div></body></html>'
    resp = Mock()
    resp.url = "https://spa.com/"
    resp.text = html
    with patch("analyzer._safe_get", return_value=resp), \
         patch("analyzer._fetch_pagespeed_insights", return_value=None), \
         patch("analyzer._guardar_analisis"):
        resultado = analizar("https://spa.com")
    assert resultado.get("spa_detected") is True, (
        "una SPA vacía se audita como si el contenido fuera el HTML crudo "
        "(scorecard basura de 1/10 en SEO/UX)"
    )


# ---------------------------------------------------------------------------
# A5 (C8) — alt="" decorativo (válido WCAG) no debe contar como sin-alt
# ---------------------------------------------------------------------------
def test_a5_alt_vacio_decorativo_no_cuenta_como_sin_alt():
    soup = BeautifulSoup(
        '<img src="a.png" alt=""><img src="b.png" alt=""><img src="c.png">',
        "html.parser",
    )
    imgs = _extraer_imagenes(soup, "https://s.com")
    # Solo la que NO tiene atributo alt debería contar.
    assert imgs["sin_alt"] == 1


# ---------------------------------------------------------------------------
# A6 (C4) — descripción en JSON-LD se debe reconocer como descripción válida
# ---------------------------------------------------------------------------
def test_a6_descripcion_jsonld_se_reconoce():
    html = ('<html><head><title>X</title>'
            '<script type="application/ld+json">'
            '{"@type":"WebSite","description":"Desc JSON-LD valida"}'
            '</script></head></html>')
    soup = BeautifulSoup(html, "html.parser")
    meta = _extraer_metadatos(soup, "https://s.com", "https://s.com")
    assert meta["description"] == "Desc JSON-LD valida", (
        "sitios modernos sin <meta name=description> pero con JSON-LD se "
        "marcan como 'falta meta description' (falso positivo)"
    )


# ---------------------------------------------------------------------------
# A7 (C11) — inputs con aria-label no deben disparar "sin labels"
# ---------------------------------------------------------------------------
def test_a7_form_con_aria_label_no_penaliza_labels():
    soup = BeautifulSoup(
        '<form><input type="email" aria-label="Email" name="e">'
        '<button>Enviar</button></form>',
        "html.parser",
    )
    forms = _extraer_forms(soup)
    score, detalles = _evaluar_accesibilidad(
        {"sin_alt": 0},
        {"h1": {"count": 1}, "jerarquia_ok": True},
        forms,
        soup,
    )
    assert "label" not in " ".join(detalles).lower(), (
        "aria-label es un label accesible válido; no debe penalizarse"
    )


# ---------------------------------------------------------------------------
# A9 (E26) — la URL debe ir URL-encodificada a PageSpeed Insights
# ---------------------------------------------------------------------------
def test_a9_psi_encoda_la_url_del_sitio():
    with patch("analyzer.requests.get") as get:
        get.return_value = Mock(status_code=200, json=lambda: {})
        _fetch_pagespeed_insights("https://s.com/?x=1&key=HACK")
        qs = parse_qs(urlparse(get.call_args[0][0]).query)
    assert qs.get("url") == ["https://s.com/?x=1&key=HACK"], (
        "la URL cruda se interpola en la query de PSI: los parámetros del "
        "sitio (p. ej. key=) contaminan la llamada"
    )
    assert qs.get("key") != ["HACK"], "el key del sitio analizado filtrado a Google"


# ---------------------------------------------------------------------------
# A3-WAF — sitio detrás de Cloudflare/DataDome/Imperva: el challenge no se audita
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("texto", [
    "<html><head><title>Just a moment...</title></head><body>Checking your browser before accessing...</body></html>",
    "<html><body>Verificando que sos humano... <script src='/cdn-cgi/challenge-platform/scripts/jsd/main.js'></script></body></html>",
    "<html><body>Access Denied. Incapsula incident ID: 1234567890</body></html>",
])
def test_a3_waf_challenge_no_se_audita(texto):
    """El HTML de un challenge WAF no es el sitio real: error claro, no scorecard."""
    with patch("analyzer.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("1.2.3.4", 80))]), \
         patch("analyzer.requests.Session") as Sess:
        sess = Sess.return_value
        resp = Mock()
        resp.is_redirect = False
        resp.status_code = 403
        resp.headers = {}
        resp.text = texto
        sess.get.return_value = resp
        with pytest.raises(ValueError) as exc:
            _safe_get("http://example.com/")
        assert "WAF" in str(exc.value), (
            "el challenge se devuelve como error genérico o se audita el HTML del WAF"
        )


def test_a3_waf_analizar_devuelve_error_claro():
    """El análisis propaga el aviso de WAF a los errores del resultado."""
    with patch(
        "analyzer._safe_get",
        side_effect=ValueError(
            "El sitio está protegido por un WAF/anti-bot (Cloudflare) — no se pudo auditar"
        ),
    ):
        resultado = analizar("http://example.com/")
    assert any("WAF" in e for e in resultado["errores"]), (
        "el usuario recibe un scorecard basura en vez del aviso de WAF"
    )


# ---------------------------------------------------------------------------
# A15 — <h1> dentro de svg/template/script no debe contar (falso conteo)
# ---------------------------------------------------------------------------
def test_a15_headings_ignoran_svg_template_script():
    html = """
    <html><body>
      <h1>Titulo real</h1>
      <script>var x = '<h1>falso en JS</h1>';</script>
      <template><h1>plantilla</h1></template>
      <svg viewBox="0 0 10 10"><text><h1>svg-h1</h1></text></svg>
      <noscript><h1>sin js</h1></noscript>
      <h2>Subtitulo</h2>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    data = _extraer_headings(soup)
    assert data["h1"]["count"] == 1, (
        f"falso conteo de H1 (svg/template/script): {data['h1']}"
    )
    assert data["h1"]["texts"] == ["Titulo real"], (
        "el H1 real debe ser el único contado"
    )


# ---------------------------------------------------------------------------
# C13 — contraste de color bajo NO medido (falso 9/10 en Accesibilidad)
# ---------------------------------------------------------------------------
def test_c13_contraste_bajo_se_penaliza():
    soup = BeautifulSoup(
        '<body style="background:#ffffff"><p style="color:#999999">'
        'Texto gris de bajo contraste</p></body>',
        "html.parser",
    )
    score, detalles = _evaluar_accesibilidad(
        {"sin_alt": 0},
        {"h1": {"count": 1}, "jerarquia_ok": True},
        {"total": 0, "con_email": 0, "lista": []},
        soup,
    )
    assert score < 10, "contraste 2.8:1 no detectado — falso 9/10 en Accesibilidad (C13)"
    assert any("contraste" in d.lower() for d in detalles), (
        "el reporte no menciona el problema de contraste"
    )


def test_c13_contraste_alto_no_se_penaliza():
    soup = BeautifulSoup(
        '<body style="background:#ffffff"><p style="color:#000000">'
        'Texto negro sobre blanco</p></body>',
        "html.parser",
    )
    score, _ = _evaluar_accesibilidad(
        {"sin_alt": 0},
        {"h1": {"count": 1}, "jerarquia_ok": True},
        {"total": 0, "con_email": 0, "lista": []},
        soup,
    )
    assert score == 10, "contraste correcto penalizado (falso positivo)"


# ---------------------------------------------------------------------------
# A40 — loop de redirects: el cuerpo de la 302 final no se audita como sitio
# ---------------------------------------------------------------------------
def test_a40_loop_de_redirects_aborta():
    """Tras 10 saltos, la 302 final no es el sitio: error claro, no HTML del redirect."""
    with patch("analyzer.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("1.2.3.4", 80))]), \
         patch("analyzer.requests.Session") as Sess:
        sess = Sess.return_value
        resp = Mock()
        resp.is_redirect = True
        resp.status_code = 302
        resp.headers = {"Location": "http://example.com/"}
        resp.text = "<html><body>Redirecting...</body></html>"
        sess.get.return_value = resp
        with pytest.raises(ValueError) as exc:
            _safe_get("http://example.com/")
        assert "redirect" in str(exc.value).lower(), (
            "se audita el cuerpo del redirect como si fuera el sitio (A40)"
        )


def test_a40_analizar_reporta_loop_de_redirects():
    """El análisis propaga el loop de redirects a errores, no devuelve scorecard."""
    with patch(
        "analyzer._safe_get",
        side_effect=ValueError(
            "Demasiados redirects al acceder a http://example.com/ — se detuvo tras 10 saltos"
        ),
    ):
        resultado = analizar("http://example.com/")
    assert any("redirect" in e.lower() for e in resultado["errores"]), (
        "el usuario recibe un scorecard en vez del aviso de loop de redirects (A40)"
    )


# ---------------------------------------------------------------------------
# A16 — hero con loading="eager"/fetchpriority="high" NO es "imagen sin lazy"
# ---------------------------------------------------------------------------
def test_a16_hero_eager_no_penaliza_sin_lazy():
    """El hero (LCP) no debe ser lazy: eager/fetchpriority=high no cuenta en sin_lazy."""
    html = """
    <html><body>
      <img src="https://s.com/hero.jpg" loading="eager" fetchpriority="high" alt="Hero">
      <img src="https://s.com/img2.jpg" alt="Sin lazy, candidata">
      <img src="https://s.com/img3.jpg" loading="lazy" alt="Con lazy">
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    data = _extraer_imagenes(soup, "https://s.com/")
    assert data["sin_lazy"] == 1, (
        f"hero con eager/fetchpriority penalizado como sin lazy (A16): {data['sin_lazy']}"
    )


def test_a16_img_sin_loading_sigue_contando_como_sin_lazy():
    """Imagen sin atributo loading (no hero) sigue siendo candidata a lazy."""
    soup = BeautifulSoup(
        '<html><body><img src="https://s.com/x.jpg" alt="X"></body></html>',
        "html.parser",
    )
    data = _extraer_imagenes(soup, "https://s.com/")
    assert data["sin_lazy"] == 1, (
        "imagen sin loading dejó de contarse como sin lazy (sobre-corrección A16)"
    )


# ---------------------------------------------------------------------------
# A31 — meta robots noindex: se avisa, no se audita como SEO normal
# ---------------------------------------------------------------------------
def test_a31_noindex_se_avisa_y_no_genera_recomendaciones_falsas():
    html = (
        '<html><head><meta name="robots" content="noindex,nofollow">'
        '<title>Una página interna</title></head><body><h1>Titulo</h1></body></html>'
    )
    soup = BeautifulSoup(html, "html.parser")
    meta = _extraer_metadatos(soup, "https://x.com/interna", "https://x.com/interna")
    assert "noindex" in (meta.get("robots") or "").lower(), (
        "robots noindex no se extrae (A31)"
    )
    score, detalles = _evaluar_seo(meta, {"h1": {"count": 1}}, soup)
    assert any("noindex" in d.lower() for d in detalles), (
        "página noindex auditada como SEO normal sin aviso (A31)"
    )
    assert not any("Falta" in d for d in detalles), (
        f"recomendaciones SEO falsas para página noindex (A31): {detalles}"
    )
    assert score == 10, f"score penalizado pese a noindex (A31): {score}"


# ---------------------------------------------------------------------------
# C15 — <html> sin atributo lang (WCAG 3.1.1): penalización leve
# ---------------------------------------------------------------------------
def _html_seo_basico(lang=None):
    lang_attr = f' lang="{lang}"' if lang else ""
    return (
        f"<html{lang_attr}><head>"
        "<title>Un titulo perfecto para una pagina de prueba</title>"
        '<meta name="description" content="Una meta description suficientemente larga para SEO basico de la pagina de prueba.">'
        '<meta property="og:title" content="Un titulo de prueba">'
        '<meta property="og:description" content="Descripcion del share.">'
        '<meta property="og:image" content="https://x.com/img.jpg">'
        '<meta name="twitter:card" content="summary_large_image">'
        '<link rel="canonical" href="https://x.com/">'
        "</head><body><h1>Titulo</h1></body></html>"
    )


def test_c15_html_sin_lang_penaliza_leve():
    soup = BeautifulSoup(_html_seo_basico(), "html.parser")
    meta = _extraer_metadatos(soup, "https://x.com", "https://x.com")
    score, detalles = _evaluar_seo(meta, {"h1": {"count": 1}}, soup)
    assert any("lang" in d.lower() for d in detalles), (
        f"falta el aviso de lang en <html> (C15): {detalles}"
    )
    assert score == 9, f"sin lang debería penalizar 1 punto (C15): {score}"


def test_c15_html_con_lang_no_penaliza():
    soup = BeautifulSoup(_html_seo_basico(lang="es"), "html.parser")
    meta = _extraer_metadatos(soup, "https://x.com", "https://x.com")
    score, detalles = _evaluar_seo(meta, {"h1": {"count": 1}}, soup)
    assert score == 10, f"html con lang penalizado (C15 control): {score} {detalles}"


# ---------------------------------------------------------------------------
# A35 — credenciales en la URL: userinfo nunca debe persistir ni loguearse
# ---------------------------------------------------------------------------
def test_a35_analizar_quita_userinfo_de_la_url():
    """https://user:pass@host entra limpio a todo el pipeline (DB, plugin, email)."""
    html = _html_seo_basico(lang="es")
    with patch("analyzer._safe_get") as sg, \
         patch("analyzer._fetch_pagespeed_insights", return_value={}), \
         patch("analyzer._guardar_analisis"):
        resp = Mock()
        resp.text = html
        resp.url = "https://ejemplo.com/"
        sg.return_value = resp
        resultado = analizar("https://user:pass@ejemplo.com/")

    assert "user:pass" not in resultado["url"], (
        "resultado['url'] persiste las credenciales de la URL (A35)"
    )
    assert resultado["url"] == "https://ejemplo.com/", resultado["url"]
    assert "user:pass" not in str(resultado.get("url_final", "")), (
        "url_final preserva las credenciales (A35)"
    )
    # El fetch recibe la URL limpia: las credenciales no viajan a la red
    assert sg.call_args[0][0] == "https://ejemplo.com/", (
        f"el fetch recibió la URL con credenciales: {sg.call_args[0][0]}"
    )


def test_a35_sanear_log_quita_userinfo_de_urls():
    """_sanear_log debe quitar user:pass@ de las URLs antes de escribir el log."""
    import app as app_module
    texto = "trace=abc url=https://user:pass@x.com/analizar?d=1 depth=1 Analizando"
    saneado = app_module._sanear_log(texto)
    assert "user:pass@" not in saneado, (
        f"el log preserva las credenciales de la URL (A35): {saneado}"
    )
    assert "https://x.com/analizar" in saneado, (
        f"la sanitización rompió la URL legítima: {saneado}"
    )


# ---------------------------------------------------------------------------
# A22 — HTTP 200 con página de error (site caído): avisar, no scorecard basura
# ---------------------------------------------------------------------------
def test_a22_pagina_de_error_en_200_avisa_sin_scorecard():
    """Una plantilla de error servida con 200 NO es el sitio: sin scorecard."""
    with patch("analyzer._safe_get") as sg:
        resp = Mock()
        resp.text = "<html><body>Error establishing a database connection</body></html>"
        resp.url = "http://x.com/"
        sg.return_value = resp
        resultado = analizar("http://x.com/")

    assert resultado["errores"], (
        "la página de error en 200 no genera aviso en errores (A22)"
    )
    assert any("error" in e.lower() for e in resultado["errores"]), resultado["errores"]
    assert resultado["scorecard"] == {}, (
        "la página de error se auditó con scorecard (A22)"
    )


def test_a22_pagina_normal_no_dispara_aviso():
    """Control: una página normal en 200 no se confunde con plantilla de error."""
    with patch("analyzer._safe_get") as sg, \
         patch("analyzer._fetch_pagespeed_insights", return_value={}), \
         patch("analyzer._guardar_analisis"):
        resp = Mock()
        resp.text = _html_seo_basico(lang="es")
        resp.url = "http://tienda.com/"
        sg.return_value = resp
        resultado = analizar("http://tienda.com/")

    assert not resultado["errores"], (
        f"falso positivo de página de error (A22): {resultado['errores']}"
    )
    assert resultado["scorecard"], "una página normal no generó scorecard"


# ---------------------------------------------------------------------------
# D16 — el ZIP del plugin debe tener nombre único por análisis (multitienda)
# ---------------------------------------------------------------------------
def _resultado_wordpress(url="https://www.ejemplo.com/"):
    return {
        "url": url,
        "scorecard": {"Rendimiento": 5, "Accesibilidad": 5, "SEO": 5, "UX": 5, "Conversión": 5},
        "meta": {
            "title": "Ejemplo",
            "og_site_name": "Ejemplo",
            "description": "Descripción de ejemplo",
        },
        "forms": {"con_email": 0},
    }


def test_d16_zip_nombre_unico_por_analisis():
    """Dos análisis del mismo dominio no pueden generar el mismo ZIP (se pisan)."""
    resultado = _resultado_wordpress()
    html = "<html><head></head><body><h1>H</h1></body></html>"
    meta = dict(resultado["meta"])
    tech = ["WordPress"]

    s1 = _generar_soluciones(dict(resultado), html, dict(meta), list(tech))
    s2 = _generar_soluciones(dict(resultado), html, dict(meta), list(tech))

    z1 = next(s["nombre"] for s in s1 if s["tipo"] == "zip")
    z2 = next(s["nombre"] for s in s2 if s["tipo"] == "zip")
    assert z1 != z2, (
        f"dos análisis del mismo dominio generan el mismo ZIP: {z1} (D16)"
    )
    assert re.match(r"^ejemplo_com_optimizer_[0-9a-f]{6}\.zip$", z1), (
        f"el nombre del ZIP no incluye el token único: {z1}"
    )


def test_d16_zip_persiste_sin_colision(monkeypatch, tmp_path):
    """Ambos ZIPs persisten en output/ — el segundo no sobrescribe al primero."""
    analisis_dir = tmp_path / "analisis"
    output_dir = tmp_path / "output"
    analisis_dir.mkdir()
    output_dir.mkdir()
    monkeypatch.setattr(analyzer, "_ANALISIS_DIR", str(analisis_dir))
    monkeypatch.setattr(analyzer, "_OUTPUT_DIR", str(output_dir))

    resultado = _resultado_wordpress()
    html = "<html><head></head><body><h1>H</h1></body></html>"
    meta = dict(resultado["meta"])
    tech = ["WordPress"]

    r1 = dict(resultado)
    r1["soluciones"] = _generar_soluciones(dict(resultado), html, dict(meta), list(tech))
    analyzer._guardar_analisis(r1)

    r2 = dict(resultado)
    r2["soluciones"] = _generar_soluciones(dict(resultado), html, dict(meta), list(tech))
    analyzer._guardar_analisis(r2)

    zips = [f for f in output_dir.iterdir() if f.name.endswith(".zip")]
    assert len(zips) == 2, (
        f"el 2º análisis pisó el ZIP del 1º: {[f.name for f in zips]} (D16)"
    )
