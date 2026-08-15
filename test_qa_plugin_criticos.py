"""
Tests QA críticos — PLUGIN WordPress generado (10 de los 25 prioritarios).

Cada test codifica el comportamiento CORRECTO del plugin que genera
`analyzer._generar_plugin_wordpress`. Los que fallan hoy son bugs reales
confirmados en el código generado (ver docs/QA-200-casos-adversariales.md).

Cobertura (casos de la matriz de 200):
  P1  E20/E21  Inyección PHP vía site_name / site_url ......... Crítico
  P2  B1       White screen por falta de mbstring ............ Crítico
  P3  B3       <img> multilínea sin lazy (regex sin /s) ....... Crítico
  P4  B4       Regex modifica contenido dentro de <script> ... Crítico
  P5  B11      Borra metas description de Yoast/RankMath ...... Crítico
  P6  B43      Agrega lazy al hero (LCP) ...................... Crítico
  P7  B28/B29  Newsletter sin handler ni nonce (emails perdidos) Crítico
  P8  B12      Duplica newsletter/CTA si el sitio ya tiene uno  Alto
  P9  B1       Sin guard de mbstring .......................... Crítico
  P10 B32/E30  PHP generado sintácticamente inválido .......... Crítico
"""
import re

import pytest

from analyzer import _generar_plugin_wordpress

SAFE_DOMAIN = "mi_sitio_com_ar"


def _gen(site_name="Mi Sitio", url="https://mi-sitio.com.ar", **extra):
    resultado = {
        "meta": {"title": site_name, "og_site_name": site_name, "description": "Descripción"},
        "url": url,
    }
    resultado.update(extra)
    return _generar_plugin_wordpress(resultado, SAFE_DOMAIN)


def _lazy_regex(code):
    """Extrae el patrón del preg_replace de lazy del PHP generado (si existe)."""
    m = re.search(r"preg_replace\('(/<img[^']*)'", code)
    return m.group(1).replace("$1", r"\1") if m else None


def _preg_patterns(code):
    """Todos los patrones de preg_replace/preg_replace_callback del PHP generado."""
    out = []
    for m in re.finditer(r"preg_replace(?:_callback)?\('", code):
        i = m.end()
        chars = []
        while i < len(code):
            ch = code[i]
            if ch == "\\":
                chars.append(ch)
                if i + 1 < len(code):
                    chars.append(code[i + 1])
                i += 2
                continue
            if ch == "'":
                break
            chars.append(ch)
            i += 1
        out.append("".join(chars))
    return out


def _php_braces_balanced(code):
    """Cuenta llaves del código PHP real, ignorando strings, comentarios y HTML."""
    depth = 0
    i = 0
    in_html = False
    n = len(code)
    while i < n:
        if in_html:
            j = code.find("<?php", i)
            if j == -1:
                return True  # resto es HTML, sin PHP
            i = j + 5
            in_html = False
            continue
        # Modo PHP
        if code.startswith("/*", i):
            j = code.find("*/", i + 2)
            if j == -1:
                return False
            i = j + 2
            continue
        if code.startswith("//", i):
            j = code.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        ch = code[i]
        if ch == "?" and i + 1 < n and code[i + 1] == ">":
            in_html = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if code[i] == "\\":
                    i += 2
                    continue
                if code[i] == quote:
                    break
                i += 1
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False
        i += 1
    return depth == 0


# ---------------------------------------------------------------------------
# P1 (E20/E21) — inyección PHP vía site_name / site_url del sitio analizado
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("payload", [
    'x */ system("id"); /*',
    'x */ eval($_GET["c"]); /*',
    'x */ passthru("cat /etc/passwd"); /*',
])
def test_p1_site_name_no_puede_inyectar_php(payload):
    code = _gen(site_name=payload)
    # El docblock del plugin debe cerrarse UNA sola vez (el legítimo). Un "*/"
    # extra proveniente del payload rompe el comentario e inyecta PHP.
    assert code.count("*/") == 1, "el payload pudo cerrar el docblock"
    for token in ("system(", "eval(", "passthru("):
        assert token not in code


def test_p1_site_url_no_puede_inyectar_php():
    code = _gen(url='https://x.com */ system("id"); /*')
    assert code.count("*/") == 1
    assert "system(" not in code


# ---------------------------------------------------------------------------
# P2 + P9 (B1) — guard de mbstring contra white screen en hosting sin mbstring
# ---------------------------------------------------------------------------
def test_p2_p9_plugin_guarda_contra_falta_de_mbstring():
    code = _gen()
    assert "function_exists('mb_substr')" in code, (
        "el plugin usa mb_substr/mb_strlen sin verificar la extensión mbstring: "
        "fatal (white screen) en hostings sin mbstring"
    )


# ---------------------------------------------------------------------------
# P3 (B3) — <img> multilínea debe recibir lazy sin romper el tag
# ---------------------------------------------------------------------------
def test_p3_lazy_funciona_en_img_multilinea():
    code = _gen()
    pattern = _lazy_regex(code)
    if pattern is None:
        pytest.skip("el plugin ya no usa regex de lazy (implementación DOM)")
    rx = re.compile(pattern, re.I)
    html = '<img\n  src="x.jpg"\n  alt="foto">'
    out = rx.sub(r'<img\1 loading="lazy">', html)
    assert "loading=\"lazy\"" in out, "la regex sin /s no matchea el <img> multilínea"
    assert out.count("<img") == 1 and out.count(">") == out.count("<img"), "tag partido"


# ---------------------------------------------------------------------------
# P4 (B4) — la reescritura no debe tocar contenido dentro de <script>/<template>
# ---------------------------------------------------------------------------
def test_p4_lazy_no_modifica_strings_dentro_de_script():
    code = _gen()
    pattern = _lazy_regex(code)
    if pattern is None:
        pytest.skip("el plugin ya no usa regex de lazy (implementación DOM)")
    rx = re.compile(pattern, re.I)
    html = '<script>var t = "<img src=a.png>";</script>'
    assert rx.sub(r'<img\1 loading="lazy">', html) == html, (
        "la regex agrega loading dentro del string JS (rompe el script)"
    )


def test_p4_no_hay_reescritura_global_de_h1():
    code = _gen()
    assert "preg_replace_callback('/<h1" not in code, (
        "la reescritura de H1 por regex global convierte <h1> dentro de "
        "scripts/templates y rompe el JS"
    )


# ---------------------------------------------------------------------------
# P5 (B11) — no borrar metas description legítimas (Yoast/RankMath)
# ---------------------------------------------------------------------------
def test_p5_no_borra_metas_description_existentes():
    code = _gen()
    assert "preg_replace('/<meta" not in code, (
        "la regex elimina TODAS las meta description (incluye las de Yoast/"
        "RankMath) y deja una sola genérica para todo el sitio"
    )


# ---------------------------------------------------------------------------
# P6 (B43) — el hero (fetchpriority) y el eager no deben volverse lazy
# ---------------------------------------------------------------------------
def test_p6_hero_y_eager_no_reciben_lazy():
    code = _gen()
    pattern = _lazy_regex(code)
    if pattern is None:
        pytest.skip("el plugin ya no usa regex de lazy (implementación DOM)")
    rx = re.compile(pattern, re.I)
    for tag in (
        '<img fetchpriority="high" src="hero.jpg">',
        '<img src="hero.jpg" loading="eager">',
        '<picture><source srcset="h.webp"><img src="hero.jpg"></picture>',
    ):
        assert rx.sub(r'<img\1 loading="lazy">', tag) == tag, (
            f"el hero/LCP recibe loading=lazy y degrada el LCP: {tag}"
        )


# ---------------------------------------------------------------------------
# P7 (B28/B29) — el newsletter debe procesar el POST (nonce + handler)
# ---------------------------------------------------------------------------
def test_p7_newsletter_tiene_handler_y_nonce():
    code = _gen()
    assert "wp_nonce_field" in code, "form sin nonce (spam)"
    assert "$_POST['email']" in code or "isset($_POST['" in code, (
        "el form hace POST a action='' pero el plugin no procesa el email: "
        "las suscripciones se pierden"
    )


# ---------------------------------------------------------------------------
# P8 (B12) — no duplicar newsletter/CTA si el sitio ya captura email
# ---------------------------------------------------------------------------
def test_p8_no_duplica_newsletter_si_el_sitio_ya_tiene():
    code = _gen(forms={"con_email": 1})  # el análisis detectó newsletter propio
    assert "do_shortcode('[newsletter]')" not in code, (
        "se agrega un segundo newsletter aunque el sitio ya tiene uno"
    )
    assert f"{SAFE_DOMAIN}_cta_flotante" not in code, (
        "se inyecta CTA flotante aunque el sitio ya tiene mecanismos de conversión"
    )


# ---------------------------------------------------------------------------
# P10 (B32/E30) — el PHP generado debe ser siempre sintácticamente válido
# ---------------------------------------------------------------------------
def test_p10_php_generado_es_sintacticamente_valido():
    code = _gen(site_name="O'Brien El Sitio & Sons")
    assert code.count("*/") == 1, "docblock mal cerrado"
    assert _php_braces_balanced(code), "llaves desbalanceadas (PHP inválido)"
    for pat in _preg_patterns(code):
        re.compile(pat)  # patrón de regex inválido => error aquí


# ---------------------------------------------------------------------------
# D19 — el plugin WordPress solo se ofrece si el sitio ES WordPress
# ---------------------------------------------------------------------------
def test_d19_plugin_wordpress_solo_si_hay_wordpress():
    from analyzer import _generar_soluciones
    base = {
        "url": "https://mi-sitio.com.ar",
        "scorecard": {"SEO": (5, [])},
        "forms": {"con_email": 0, "total": 0, "lista": []},
        "meta": {"title": "Mi Sitio", "og_site_name": "Mi Sitio", "description": "Descripción de ejemplo del sitio"},
    }
    meta = {"title": "Mi Sitio", "description": "Descripción de ejemplo del sitio"}
    sol = _generar_soluciones(base, "<html></html>", meta, tech=[])
    nombres = [s["nombre"] for s in sol]
    assert not any(n.endswith("optimizer.zip") for n in nombres), (
        "se genera el plugin WordPress para un sitio que NO es WordPress (D19): "
        "el cliente Wix/Squarespace recibe un ZIP inútil"
    )
    sol_wp = _generar_soluciones(base, "<html></html>", meta, tech=["WordPress"])
    assert any(n.endswith("optimizer.zip") for n in [s["nombre"] for s in sol_wp]), (
        "con WordPress detectado el plugin debería ofrecerse"
    )


# ---------------------------------------------------------------------------
# D1 — sin CTA/trust bar de marca en sitios de rubro sensible (salud/legal/financiero)
# ---------------------------------------------------------------------------
def test_d1_sitio_sensible_sin_cta_de_marca():
    code = _gen(meta={
        "title": "Clínica Dental Dr. López",
        "og_site_name": "Clínica Dental",
        "description": "Atención odontológica y salud dental en el centro",
    })
    assert f"{SAFE_DOMAIN}_cta_flotante" not in code, (
        "se inyecta el CTA flotante de marca sobre un sitio de salud (D1): "
        "riesgo reputacional/legal"
    )
    assert f"{SAFE_DOMAIN}_trust_bar" not in code, (
        "se inyecta la trust bar de marca sobre un sitio de salud (D1)"
    )
    # Control: un sitio neutral sí lleva CTA (el gating no debe quitarlo de todos)
    assert f"{SAFE_DOMAIN}_cta_flotante" in _gen(), (
        "el gating por rubro apagó el CTA también en sitios neutrales"
    )


# ---------------------------------------------------------------------------
# D21 — el newsletter debe pedir consentimiento + política (Ley 25.326/GDPR)
# ---------------------------------------------------------------------------
def test_d21_newsletter_pide_consentimiento():
    code = _gen()
    assert 'type="checkbox"' in code, "el form no tiene checkbox de consentimiento (D21)"
    assert "_consent" in code, "el handler no verifica el consentimiento (D21)"
    assert "privacidad" in code.lower(), "el form no referencia la política de privacidad (D21)"


# ---------------------------------------------------------------------------
# A6 — sitio multiidioma (WPML/Polylang): no borrar metas description por idioma
# ---------------------------------------------------------------------------
def test_a6_no_borra_metas_description_por_idioma():
    code = _gen()
    assert "removeChild($meta)" not in code, (
        "el plugin borra TODAS las meta description (WPML/Polylang tienen "
        "una por idioma) y deja una sola genérica (A6)"
    )
    assert "count($descripciones) === 0" in code, (
        "la meta description propia debe inyectarse solo si el sitio no tiene ninguna"
    )


# ---------------------------------------------------------------------------
# B25 — defer no debe romper widgets de chat/CRM con document.write
# ---------------------------------------------------------------------------
def test_b25_defer_excluye_widgets_de_terceros():
    code = _gen()
    assert "jquery" in code, "el defer debe seguir excluyendo jQuery"
    for widget in ("tawk", "crisp", "hubspot", "intercom", "zendesk"):
        assert widget in code, (
            f"el defer no excluye el widget de terceros {widget} — "
            "document.write + defer rompe el widget (B25)"
        )


# ---------------------------------------------------------------------------
# E22 — safe_domain con dígito inicial genera PHP inválido (familia P10)
# ---------------------------------------------------------------------------
def test_e22_safe_domain_con_digito_genera_php_valido():
    """2do.com.ar -> safe_domain '2do_com_ar' -> function 2do_...() (PHP inválido)."""
    import io
    import zipfile
    from analyzer import _generar_soluciones

    base = {
        "url": "https://2do.com.ar",
        "scorecard": {"SEO": (5, [])},
        "forms": {"con_email": 0, "total": 0, "lista": []},
        "meta": {"title": "2do Sitio", "og_site_name": "2do Sitio", "description": "Descripción de ejemplo"},
    }
    meta = {"title": "2do Sitio", "description": "Descripción de ejemplo"}
    sol = _generar_soluciones(base, "<html></html>", meta, tech=["WordPress"])
    zip_sol = next(s for s in sol if s["nombre"].endswith("optimizer.zip"))
    with zipfile.ZipFile(io.BytesIO(zip_sol["contenido"])) as zf:
        code = zf.read(zf.namelist()[0]).decode("utf-8")
    assert not re.search(r"function\s+\d", code), (
        "safe_domain con dígito inicial genera function 2do_...() (PHP inválido, E22)"
    )
    funcs = re.findall(r"function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
    assert funcs, "no se encontraron funciones en el plugin generado"
    assert _php_braces_balanced(code), "llaves desbalanceadas (PHP inválido)"


# ---------------------------------------------------------------------------
# B19 — document.write inline: el defer global se desactiva (página vaciada)
# ---------------------------------------------------------------------------
def test_b19_document_write_inline_desactiva_defer():
    """HTML con document.write inline -> el plugin NO agrega defer global (B19)."""
    import io
    import zipfile
    from analyzer import _generar_soluciones

    base = {
        "url": "https://mi-sitio.com.ar",
        "scorecard": {"SEO": (5, [])},
        "forms": {"con_email": 0, "total": 0, "lista": []},
        "meta": {"title": "Mi Sitio", "og_site_name": "Mi Sitio", "description": "Descripción"},
    }
    meta = {"title": "Mi Sitio", "description": "Descripción"}

    def _code(html):
        sol = _generar_soluciones(base, html, meta, tech=["WordPress"])
        zip_sol = next(s for s in sol if s["nombre"].endswith("optimizer.zip"))
        with zipfile.ZipFile(io.BytesIO(zip_sol["contenido"])) as zf:
            return zf.read(zf.namelist()[0]).decode("utf-8")

    html_con_dw = r"<html><head><script>document.write('<script src=\"lib.js\"><\/script>');</script></head><body><h1>H</h1></body></html>"
    code = _code(html_con_dw)
    assert "script_loader_tag" not in code, (
        "defer aplicado pese a document.write inline: página vaciada en algunos browsers (B19)"
    )

    # Control: sin document.write el defer sigue generándose (B25 intacto)
    code_ok = _code("<html><body><img src='x.jpg' alt='X'></body></html>")
    assert "script_loader_tag" in code_ok, (
        "el defer dejó de generarse para sitios sin document.write (sobre-corrección B19)"
    )
