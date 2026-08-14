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
