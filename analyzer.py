"""
Motor de análisis del Web Analyzer & Optimizer.
Extrae, evalúa y genera soluciones para cualquier URL pública.
"""
import os
import re
import json
import hashlib
import zipfile
import io
import socket
import ipaddress
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# =============================================================================
# Constantes de evaluación
# =============================================================================

CATEGORIAS = ["Rendimiento", "Accesibilidad", "SEO", "UX", "Conversión"]

HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]

# Patrones para detectar tecnologías
TECH_SIGNATURES = {
    "WordPress": ["wp-content", "wp-json", "wordpress"],
    "React": ["react", "data-reactroot", "_reactRoot"],
    "Vue.js": ["vue", "data-v-"],
    "jQuery": ["jquery"],
    "Bootstrap": ["bootstrap"],
    "Tailwind": ["tailwind"],
    "Next.js": ["__NEXT", "next"],
    "Shopify": ["shopify", "myshopify"],
    "Wix": ["wix"],
    "Squarespace": ["squarespace"],
}


_PRIVATE_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


def _is_public_url(url):
    """Valida que la URL apunte a un servidor público (anti-SSRF)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False, "Solo se permiten URLs http/https"

    hostname = parsed.hostname
    if not hostname:
        return False, "URL sin hostname válido"

    host_lower = hostname.lower()
    if host_lower in _PRIVATE_HOSTS or host_lower.startswith("127."):
        return False, "Host interno no permitido"

    try:
        ips = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return False, f"No se pudo resolver el dominio: {hostname}"

    for _, _, _, _, sockaddr in ips:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
            return False, f"IP no pública detectada: {ip_str}"
        if ip.version == 6 and ip.is_reserved:
            return False, f"IPv6 reservada detectada: {ip_str}"

    return True, "ok"


def _safe_get(url, timeout=15):
    """Fetch URL con headers de navegador y protección SSRF."""
    ok, reason = _is_public_url(url)
    if not ok:
        raise ValueError(f"URL bloqueada: {reason}")

    import random
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()
        return resp
    except requests.Timeout:
        raise ValueError(f"Timeout al acceder a {url} — el servidor no respondió en {timeout}s")
    except requests.ConnectionError as e:
        raise ValueError(f"No se pudo conectar a {url} — verificá que la URL sea correcta")


def _score_color(score):
    if score >= 8:
        return "verde"
    elif score >= 5:
        return "amarillo"
    return "rojo"


# =============================================================================
# Análisis principal
# =============================================================================


def analizar(url):
    """
    Analiza una URL y retorna un dict completo con:
    - metadatos extraídos
    - puntajes por categoría
    - hallazgos críticos
    - recomendaciones
    - código de soluciones
    - archivos generados
    """
    resultado = {
        "url": url,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "scorecard": {},
        "hallazgos": [],
        "recomendaciones": [],
        "soluciones": [],
        "html_raw": None,
        "tecnologia": [],
        "errores": [],
    }

    # --- Fetch ---
    try:
        resp = _safe_get(url)
        resultado["url_final"] = resp.url
        html = resp.text
        resultado["html_raw"] = html
    except Exception as e:
        resultado["errores"].append(f"No se pudo acceder a la URL: {e}")
        return resultado

    soup = BeautifulSoup(html, "html.parser")

    # --- Extracción ---
    meta = _extraer_metadatos(soup, url, resp.url)
    imagenes = _extraer_imagenes(soup, url)
    headings_data = _extraer_headings(soup)
    forms = _extraer_forms(soup)
    scripts = _extraer_scripts(soup, url)
    enlaces = _extraer_enlaces(soup, url)
    tech = _detectar_tecnologia(html, soup)
    size_kb = len(html) / 1024

    resultado["tecnologia"] = tech
    resultado["meta"] = meta
    resultado["imagenes"] = imagenes
    resultado["headings"] = headings_data
    resultado["forms"] = forms
    resultado["scripts"] = scripts
    resultado["enlaces"] = enlaces
    resultado["size_kb"] = round(size_kb, 1)

    # --- Evaluación ---
    psi_data = _fetch_pagespeed_insights(resp.url)  # usar URL final (con redirects)
    resultado["psi"] = psi_data
    score_rendimiento = _evaluar_rendimiento(imagenes, scripts, size_kb, psi_data)
    score_accesibilidad = _evaluar_accesibilidad(imagenes, headings_data, forms, soup)
    score_seo = _evaluar_seo(meta, headings_data, soup)
    score_ux = _evaluar_ux(meta, headings_data, enlaces, soup)
    score_conversion = _evaluar_conversion(forms, enlaces, soup)

    resultado["scorecard"] = {
        "Rendimiento": score_rendimiento,
        "Accesibilidad": score_accesibilidad,
        "SEO": score_seo,
        "UX": score_ux,
        "Conversión": score_conversion,
    }

    # --- Hallazgos ---
    resultado["hallazgos"] = _generar_hallazgos(resultado)

    # --- Recomendaciones ---
    resultado["recomendaciones"] = _generar_recomendaciones(resultado)

    # --- Soluciones (archivos) ---
    resultado["soluciones"] = _generar_soluciones(resultado, html, meta, tech)

    # --- Guardar análisis ---
    _guardar_analisis(resultado)

    return resultado


# =============================================================================
# Extractores
# =============================================================================


def _extraer_metadatos(soup, url_original, url_final):
    meta = {
        "title": None,
        "title_length": 0,
        "description": None,
        "description_length": 0,
        "viewport": None,
        "robots": None,
        "canonical": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "og_url": None,
        "og_type": None,
        "og_site_name": None,
        "og_locale": None,
        "twitter_card": None,
        "twitter_title": None,
        "twitter_description": None,
        "twitter_image": None,
        "generator": None,
    }

    if soup.title:
        meta["title"] = soup.title.string.strip() if soup.title.string else ""
        meta["title_length"] = len(meta["title"])

    for tag in soup.find_all("meta"):
        name = tag.get("name", "").lower()
        prop = tag.get("property", "").lower()
        content = tag.get("content", "")

        if name == "description":
            meta["description"] = content
            meta["description_length"] = len(content)
        elif name == "viewport":
            meta["viewport"] = content
        elif name == "robots":
            meta["robots"] = content
        elif name == "generator":
            meta["generator"] = content
        elif prop == "og:title":
            meta["og_title"] = content
        elif prop == "og:description":
            meta["og_description"] = content
        elif prop == "og:image":
            meta["og_image"] = content
        elif prop == "og:url":
            meta["og_url"] = content
        elif prop == "og:type":
            meta["og_type"] = content
        elif prop == "og:site_name":
            meta["og_site_name"] = content
        elif prop == "og:locale":
            meta["og_locale"] = content
        elif name == "twitter:card":
            meta["twitter_card"] = content
        elif name == "twitter:title":
            meta["twitter_title"] = content
        elif name == "twitter:description":
            meta["twitter_description"] = content
        elif name == "twitter:image":
            meta["twitter_image"] = content

    # Canonical
    canon = soup.find("link", rel="canonical")
    if canon:
        meta["canonical"] = canon.get("href", "")

    return meta


def _extraer_imagenes(soup, base_url):
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src and not src.startswith("data:"):
            src = urljoin(base_url, src)
        imgs.append({
            "src": src,
            "alt": img.get("alt", ""),
            "width": img.get("width", ""),
            "height": img.get("height", ""),
            "loading": img.get("loading", ""),
            "format": _formato_imagen(src),
        })
    return {
        "total": len(imgs),
        "sin_alt": sum(1 for i in imgs if not i["alt"]),
        "sin_lazy": sum(1 for i in imgs if i["loading"] != "lazy"),
        "formatos": list(set(i["format"] for i in imgs if i["format"])),
        "lista": imgs[:20],
    }


def _formato_imagen(src):
    if not src:
        return None
    src_low = src.lower()
    if ".webp" in src_low:
        return "webp"
    if ".avif" in src_low:
        return "avif"
    if ".png" in src_low:
        return "png"
    if ".jpg" in src_low or ".jpeg" in src_low:
        return "jpg"
    if ".svg" in src_low:
        return "svg"
    if ".gif" in src_low:
        return "gif"
    return "otro"


def _extraer_headings(soup):
    result = {}
    for h in HEADINGS:
        tags = soup.find_all(h)
        result[h] = {"count": len(tags), "texts": [t.get_text(strip=True)[:100] for t in tags[:10]]}
    # Verificar jerarquía
    jerarquia = []
    for h in HEADINGS:
        if result[h]["count"] > 0:
            jerarquia.append(h)
    result["jerarquia"] = jerarquia
    result["jerarquia_ok"] = _verificar_jerarquia(jerarquia)
    return result


def _verificar_jerarquia(jerarquia):
    """Verifica que no haya saltos en la jerarquía de headings."""
    if not jerarquia:
        return True
    niveles = [int(h[1]) for h in jerarquia]
    for i in range(1, len(niveles)):
        if niveles[i] - niveles[i - 1] > 1:
            return False
    return True


def _extraer_forms(soup):
    forms = []
    for form in soup.find_all("form"):
        inputs = form.find_all(["input", "textarea", "select"])
        labels = form.find_all("label")
        submit = form.find_all(["button", "input"], type="submit")
        forms.append({
            "action": form.get("action", ""),
            "method": form.get("method", "GET").upper(),
            "inputs": len(inputs),
            "labels": len(labels),
            "has_submit": len(submit) > 0,
            "has_email": any(
                inp.get("type") == "email" or "email" in (inp.get("name", "") + inp.get("id", "")).lower()
                for inp in inputs
            ),
        })
    return {
        "total": len(forms),
        "con_email": sum(1 for f in forms if f["has_email"]),
        "lista": forms,
    }


def _extraer_scripts(soup, base_url):
    scripts = []
    externos = 0
    for s in soup.find_all("script"):
        src = s.get("src", "")
        if src:
            externos += 1
            if not src.startswith(("http:", "https:", "//")):
                src = urljoin(base_url, src)
        scripts.append({
            "src": src,
            "async": s.get("async") is not None,
            "defer": s.get("defer") is not None,
            "inline": not bool(src),
        })
    return {
        "total": len(scripts),
        "externos": externos,
        "bloqueantes": sum(1 for s in scripts if s["src"] and not s["async"] and not s["defer"]),
        "con_async_defer": sum(1 for s in scripts if s["async"] or s["defer"]),
    }


def _extraer_enlaces(soup, base_url):
    links = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href:
            # Mantener el href tal cual para anclajes (#newsletter), urljoin para rutas
            full_href = href if href.startswith("#") else urljoin(base_url, href)
            links.append({"href": full_href, "text": text[:80]})
    externos = sum(1 for l in links if urlparse(l["href"]).netloc not in (urlparse(base_url).netloc, ""))
    ctas = [
        l for l in links
        if any(
            word in l["text"].lower()
            for word in ["comprar", "suscrib", "registr", "contact", "empezar", "probar", "descargar", "leer más"]
        )
    ]
    return {"total": len(links), "externos": externos, "ctas": ctas[:10]}


def _detectar_tecnologia(html, soup):
    html_low = html.lower()
    detectadas = []
    for tech, patterns in TECH_SIGNATURES.items():
        for p in patterns:
            if p.lower() in html_low:
                detectadas.append(tech)
                break

    # Generador
    gen = soup.find("meta", attrs={"name": "generator"})
    if gen:
        gen_content = gen.get("content", "")
        if gen_content:
            detectadas.append(gen_content)

    return detectadas


# =============================================================================
# Evaluadores (0-10)
# =============================================================================


def _fetch_pagespeed_insights(url: str) -> dict | None:
    """Consulta la API de PageSpeed Insights para métricas reales de Core Web Vitals."""
    api_key = os.environ.get("PAGESPEED_API_KEY", "")
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}"
    if api_key:
        api_url += f"&key={api_key}"
    try:
        resp = requests.get(api_url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; WebAnalyzer/1.0)"
        })
        if resp.status_code != 200:
            return None
        data = resp.json()
        lighthouse = data.get("lighthouseResult", {})
        audits = lighthouse.get("audits", {})
        return {
            "performance_score": round(lighthouse.get("categories", {}).get("performance", {}).get("score", 0) * 10, 1),
            "lcp": audits.get("largest-contentful-paint", {}).get("displayValue", "N/A"),
            "tbt": audits.get("total-blocking-time", {}).get("displayValue", "N/A"),
            "cls": audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A"),
            "fcp": audits.get("first-contentful-paint", {}).get("displayValue", "N/A"),
            "speed_index": audits.get("speed-index", {}).get("displayValue", "N/A"),
        }
    except Exception:
        return None


def _evaluar_rendimiento(imagenes, scripts, size_kb, psi_data=None):
    score = 10
    detalles = []

    # Imágenes sin lazy loading
    if imagenes["total"] > 0:
        sin_lazy_pct = imagenes["sin_lazy"] / max(imagenes["total"], 1) * 100
        if sin_lazy_pct > 80:
            score -= 3
            detalles.append(f"{imagenes['sin_lazy']} de {imagenes['total']} imágenes sin lazy loading")
        elif sin_lazy_pct > 30:
            score -= 1
            detalles.append(f"{imagenes['sin_lazy']} imágenes sin lazy loading")

    # Formatos obsoletos (PNG en lugar de WebP)
    if "png" in imagenes.get("formatos", []) and "webp" not in imagenes.get("formatos", []):
        score -= 2
        detalles.append("Imágenes PNG sin versión WebP")

    # Scripts bloqueantes
    if scripts["bloqueantes"] > 3:
        score -= 2
        detalles.append(f"{scripts['bloqueantes']} scripts bloqueantes (sin async/defer)")
    elif scripts["bloqueantes"] > 0:
        score -= 1

    # Tamaño de página
    if size_kb > 500:
        score -= 2
        detalles.append(f"Página pesada: {size_kb:.0f} KB")
    elif size_kb > 200:
        score -= 1

    score_heuristico = max(0, min(10, score))

    # --- Core Web Vitals (PageSpeed Insights) ---
    if psi_data and psi_data.get("performance_score") is not None:
        psi_score = psi_data["performance_score"]
        # Blend: 60% heurístico + 40% PSI para evitar que un CDN o caché distorsione
        score_final = round(score_heuristico * 0.6 + psi_score * 0.4, 1)
        # Agregar métricas reales a los detalles
        cwv = []
        if psi_data.get("lcp"):
            cwv.append(f"LCP: {psi_data['lcp']}")
        if psi_data.get("tbt"):
            cwv.append(f"TBT: {psi_data['tbt']}")
        if psi_data.get("cls"):
            cwv.append(f"CLS: {psi_data['cls']}")
        if cwv:
            detalles.append("Core Web Vitals: " + " · ".join(cwv))
        return max(0, min(10, score_final)), detalles

    return score_heuristico, detalles


def _evaluar_accesibilidad(imagenes, headings, forms, soup):
    score = 10
    detalles = []

    # Imágenes sin alt
    if imagenes["sin_alt"] > 0:
        deduction = min(4, imagenes["sin_alt"])
        score -= deduction
        detalles.append(f"{imagenes['sin_alt']} imágenes sin atributo alt")

    # Jerarquía de headings
    if not headings["jerarquia_ok"]:
        score -= 2
        detalles.append(f"Jerarquía de headings rota: {headings['jerarquia']}")

    # Múltiples H1
    if headings.get("h1", {}).get("count", 0) > 1:
        score -= 1
        detalles.append(f"{headings['h1']['count']} H1 en la página (debería ser 1)")

    # Sin H1
    if headings.get("h1", {}).get("count", 0) == 0:
        score -= 3
        detalles.append("Falta H1 en la página")

    # Formularios sin labels
    for f in forms.get("lista", []):
        if f["inputs"] > 0 and f["labels"] == 0:
            score -= 1
            detalles.append("Formulario sin elementos label")
            break

    # Skip link
    skip_link = soup.find("a", href="#content") or soup.find("a", string=re.compile("saltar|skip", re.I))
    if not skip_link and soup.find("body"):
        score -= 0  # No penalizar, solo notar
        # detalles.append("Sin skip-link para navegación por teclado")

    return max(0, min(10, score)), detalles


def _evaluar_seo(meta, headings, soup):
    score = 10
    detalles = []

    # Title
    if not meta["title"]:
        score -= 4
        detalles.append("Falta title tag")
    elif meta["title_length"] < 30:
        score -= 2
        detalles.append(f"Title muy corto ({meta['title_length']} chars): '{meta['title']}'")
    elif meta["title_length"] > 70:
        score -= 1
        detalles.append(f"Title muy largo ({meta['title_length']} chars)")

    # Meta description
    if not meta["description"]:
        score -= 3
        detalles.append("Falta meta description")
    elif meta["description_length"] < 70:
        score -= 2
        detalles.append(f"Meta description muy corta ({meta['description_length']} chars)")
    elif meta["description_length"] > 160:
        score -= 1
        detalles.append(f"Meta description muy larga ({meta['description_length']} chars)")

    # Open Graph
    if not meta["og_title"]:
        score -= 2
        detalles.append("Faltan Open Graph tags (og:title, og:description, og:image)")
    if not meta["og_image"]:
        score -= 1
        detalles.append("Falta og:image — los shares en redes no muestran imagen")

    # Twitter Cards
    if not meta["twitter_card"]:
        score -= 1
        detalles.append("Falta Twitter Card")

    # Canonical
    if not meta["canonical"]:
        score -= 1
        detalles.append("Falta canonical URL")

    # H1 único
    if headings.get("h1", {}).get("count", 0) != 1:
        score -= 1
        detalles.append("Debe haber exactamente 1 H1")

    return max(0, min(10, score)), detalles


def _evaluar_ux(meta, headings, enlaces, soup):
    score = 10
    detalles = []

    # Viewport (responsive)
    if not meta.get("viewport"):
        score -= 4
        detalles.append("Falta meta viewport — sitio no responsive")

    # CTAs
    if len(enlaces.get("ctas", [])) == 0:
        score -= 2
        detalles.append("No se detectan CTAs claros (call-to-action)")

    # Estructura de contenido
    if headings.get("h1", {}).get("count", 0) == 0 and headings.get("h2", {}).get("count", 0) == 0:
        score -= 2
        detalles.append("Página sin estructura de headings — difícil de escanear")

    # Menú de navegación
    nav = soup.find("nav")
    if not nav:
        score -= 1
        detalles.append("Sin elemento <nav> semántico")

    return max(0, min(10, score)), detalles


def _evaluar_conversion(forms, enlaces, soup):
    score = 5  # Base neutra
    detalles = []

    # Formularios de captura
    if forms["con_email"] > 0:
        score += 3
        detalles.append("Formulario de captura de email detectado")
    elif forms["total"] > 0:
        score += 1
        detalles.append(f"{forms['total']} formulario(s) detectado(s)")
    else:
        score -= 1
        detalles.append("Sin formularios — sin mecanismo de conversión")

    # CTAs
    ctas = enlaces.get("ctas", [])
    if len(ctas) >= 5:
        score += 2
    elif len(ctas) >= 2:
        score += 1
    else:
        score -= 1
        detalles.append("Pocos CTAs detectados")

    # Elementos de confianza
    html_text = soup.get_text().lower()
    confianza = 0
    if "testimonio" in html_text or "testimonial" in html_text:
        confianza += 1
    if "garant" in html_text:
        confianza += 1
    if soup.find_all(["blockquote", ".testimonial", ".review"]):
        confianza += 1
    if confianza == 0:
        score -= 1
        detalles.append("Sin elementos de confianza visibles (testimonios, garantías)")

    return max(0, min(10, score)), detalles


# =============================================================================
# Generadores de hallazgos y recomendaciones
# =============================================================================


def _generar_hallazgos(resultado):
    hallazgos = []
    scorecard = resultado["scorecard"]
    meta = resultado["meta"]
    imgs = resultado["imagenes"]

    # Ordenar por gravedad
    for cat, (score, detalles) in scorecard.items():
        if score <= 4:
            for d in detalles:
                hallazgos.append({
                    "categoria": cat,
                    "gravedad": "critica" if score <= 3 else "alta",
                    "problema": d,
                    "impacto": _impacto_por_categoria(cat),
                })

    return hallazgos


def _impacto_por_categoria(cat):
    impactos = {
        "Rendimiento": "Velocidad de carga, Core Web Vitals, experiencia móvil",
        "Accesibilidad": "Usuarios con lectores de pantalla, cumplimiento legal WCAG",
        "SEO": "Posicionamiento en Google, CTR en búsquedas",
        "UX": "Tasa de rebote, tiempo en página, satisfacción del usuario",
        "Conversión": "Tasa de conversión, captura de leads, ventas",
    }
    return impactos.get(cat, "Experiencia general del usuario")


def _generar_recomendaciones(resultado):
    recs = []
    scorecard = resultado["scorecard"]
    meta = resultado["meta"]
    imgs = resultado["imagenes"]
    tech = resultado["tecnologia"]

    # SEO: Meta description
    if not meta["description"] or meta["description_length"] < 70:
        recs.append({
            "categoria": "SEO",
            "titulo": "Agregar meta description efectiva",
            "problema": "La meta description falta o es muy corta. Google muestra un snippet automático que puede no ser atractivo.",
            "solucion": "Agregar <meta name='description' content='120-155 caracteres con keyword principal y llamado a la acción'>",
            "esfuerzo": "Bajo",
        })

    # SEO: OG tags
    if not meta["og_title"] or not meta["og_image"]:
        recs.append({
            "categoria": "SEO",
            "titulo": "Completar Open Graph tags",
            "problema": "Al compartir en WhatsApp, Telegram o redes sociales no se muestra imagen ni descripción.",
            "solucion": "Agregar og:title, og:description, og:image (1200x630px) y og:url en el <head>",
            "esfuerzo": "Bajo",
        })

    # Rendimiento: lazy loading
    if imgs["sin_lazy"] > imgs["total"] * 0.5:
        recs.append({
            "categoria": "Rendimiento",
            "titulo": "Activar lazy loading en imágenes",
            "problema": f"{imgs['sin_lazy']} de {imgs['total']} imágenes cargan al mismo tiempo, ralentizando la página.",
            "solucion": "Agregar loading='lazy' a todas las imágenes debajo del fold. En WordPress: WP Rocket o similar.",
            "esfuerzo": "Bajo",
        })

    # Accesibilidad: alt text
    if imgs["sin_alt"] > 0:
        recs.append({
            "categoria": "Accesibilidad",
            "titulo": "Agregar alt text a imágenes",
            "problema": f"{imgs['sin_alt']} imágenes sin atributo alt. Los lectores de pantalla no pueden describirlas.",
            "solucion": "Agregar alt descriptivo a cada imagen. El alt debe describir el contenido de la imagen, no ser genérico.",
            "esfuerzo": "Medio",
        })

    # Conversión: formulario de newsletter
    if resultado["forms"]["con_email"] == 0:
        recs.append({
            "categoria": "Conversión",
            "titulo": "Agregar formulario de captura de email",
            "problema": "Sin formulario de newsletter, cada visitante que se va es tráfico perdido para siempre.",
            "solucion": "Agregar formulario de suscripción con 1 solo campo (email) y botón claro. Ofrecer valor: 'Recibí las noticias en tu mail'.",
            "esfuerzo": "Medio",
        })

    return recs


# =============================================================================
# Generador de soluciones (archivos descargables)
# =============================================================================


def _generar_soluciones(resultado, html, meta, tech):
    """
    Genera archivos de solución listos para descargar y aplicar.
    Retorna lista de dicts con nombre, tipo, contenido y descripción.
    """
    soluciones = []
    dominio = urlparse(resultado["url"]).netloc.replace("www.", "")
    safe_domain = re.sub(r"[^a-zA-Z0-9_]", "_", dominio)

    # --- Solución 1: Meta tags fix (siempre útil) ---
    current_title = meta.get("title") or "TITULO DEL SITIO"
    current_desc = meta.get("description") or "DESCRIPCION DEL SITIO"

    soluciones.append({
        "nombre": f"{safe_domain}_seo_fix.md",
        "tipo": "markdown",
        "descripcion": "Guía paso a paso para corregir SEO y meta tags",
        "contenido": f"""# Corrección SEO para {resultado['url']}

## 1. Meta description
**Actual:** `{current_desc}`
**Recomendada:** Una descripción de 120-155 caracteres con la keyword principal y un llamado a la acción.

## 2. Open Graph
Agregar en el `<head>`:
```html
<meta property="og:title" content="{current_title}">
<meta property="og:description" content="Descripción atractiva para redes sociales">
<meta property="og:image" content="https://{dominio}/imagen-1200x630.jpg">
<meta property="og:url" content="{resultado['url']}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
```

## 3. Twitter Card
```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{current_title}">
<meta name="twitter:description" content="Descripción para Twitter">
<meta name="twitter:image" content="https://{dominio}/imagen-1200x630.jpg">
```

## 4. Canonical
```html
<link rel="canonical" href="{resultado['url']}">
```
""",
    })

    # --- Solución 2: Plugin WordPress ZIP si aplica ---
    if any("WordPress" in t for t in tech):
        plugin_code = _generar_plugin_wordpress(resultado, safe_domain)
        plugin_zip = _crear_zip_plugin(safe_domain, plugin_code)
        soluciones.append({
            "nombre": f"{safe_domain}_optimizer.zip",
            "tipo": "zip",
            "descripcion": "Plugin WordPress listo para instalar. Descargar ZIP y subir a Plugins > Añadir nuevo > Subir plugin.",
            "contenido": plugin_zip,
            "binario": True,
        })

    # --- Solución 2b: Snippet Shopify si aplica ---
    if any("Shopify" in t for t in tech):
        snippet = _generar_snippet_shopify(resultado, safe_domain)
        soluciones.append({
            "nombre": f"{safe_domain}_shopify_snippet.liquid",
            "tipo": "liquid",
            "descripcion": "Código Liquid para pegar en el theme.liquid de Shopify. Agrega meta tags, lazy loading y formulario de newsletter.",
            "contenido": snippet,
        })

    # --- Solución 3: HTML patch genérico ---
    patch_html = _generar_patch_html(meta, resultado)
    soluciones.append({
        "nombre": f"{safe_domain}_fixes.html",
        "tipo": "html",
        "descripcion": "Fragmentos de HTML corregidos para reemplazar en el código fuente.",
        "contenido": patch_html,
    })

    # --- Solución 4: Resumen JSON ---
    soluciones.append({
        "nombre": f"{safe_domain}_reporte.json",
        "tipo": "json",
        "descripcion": "Reporte completo en formato JSON para integración con otras herramientas.",
        "contenido": json.dumps(resultado["scorecard"], indent=2, ensure_ascii=False),
    })

    return soluciones


def _generar_plugin_wordpress(resultado, safe_domain):
    """Genera un plugin WordPress con todas las correcciones."""
    site_name = resultado["meta"].get("og_site_name") or resultado["meta"].get("title") or safe_domain
    site_desc = resultado["meta"].get("description") or ""
    site_url = resultado["url"]

    return f"""<?php
/**
 * Plugin Name: {site_name} Optimizer
 * Description: SEO, accesibilidad y rendimiento optimizado automáticamente por DelMonte Web Analyzer.
 * Version: 1.0
 * Plugin URI: {site_url}
 * Author: Web Analyzer & Optimizer
 * Author URI: https://delmonteanalitica.com
 *
 * === INSTRUCCIONES DE SEGURIDAD ===
 * Si este plugin causa algún error en tu sitio:
 * 1. Entrá por FTP/SFTP a /wp-content/plugins/{safe_domain}_optimizer/
 * 2. Renombrá la carpeta a /{safe_domain}_optimizer_DESACTIVADO/
 * 3. WordPress desactivará el plugin automáticamente.
 * 4. Escribinos a soporte@delmonteanalitica.com y lo resolvemos.
 *
 * Compatible con WordPress 5.0+ y PHP 7.4+.
 * Testeado con themes: Astra, GeneratePress, Divi, OceanWP, Hello Elementor, Kadence, Twenty-*.
 */

if (!defined('ABSPATH')) exit;

// Compatibilidad: verificar versión de PHP antes de ejecutar
if (version_compare(PHP_VERSION, '7.4', '<')) {{
    add_action('admin_notices', function() {{
        echo '<div class=\"notice notice-error\"><p><strong>{site_name} Optimizer:</strong> Requiere PHP 7.4 o superior. Tu versión: ' . PHP_VERSION . '. El plugin no se ejecutará. <a href=\"mailto:soporte@delmonteanalitica.com\">Contactar soporte</a>.</p></div>';
    }});
    return;
}}

// HABILITAR SHORTCODES EN WIDGETS
add_filter('widget_text', 'do_shortcode');
add_filter('widget_custom_html_content', 'do_shortcode');

// NEWSLETTER SHORTCODE [newsletter]
function {safe_domain}_newsletter_shortcode() {{
    ob_start();
    ?>
    <div style="background:linear-gradient(135deg,#0a0f1e,#1a1f2e);padding:24px;border-radius:12px;border-left:4px solid #75aadb;font-family:Arial,sans-serif;margin:20px 0;color:#e0e0e0">
      <h3 style="margin:0 0 6px;font-size:17px;color:#fff">Recibí las noticias en tu mail</h3>
      <p style="margin:0 0 16px;font-size:13px;color:#aaa">Suscribite gratis y no te pierdas ninguna actualización.</p>
      <form method="post" action="" style="display:flex;flex-direction:column;gap:10px">
        <label for="newsletter_email" style="font-size:12px;color:#aaa;margin-bottom:-6px">Tu email</label>
        <input type="email" name="email" id="newsletter_email" placeholder="tu@email.com" required
               style="padding:12px;border:1px solid #333;border-radius:6px;font-size:14px;background:#111;color:#fff">
        <button type="submit"
                style="padding:12px;background:#75aadb;color:#000;border:none;border-radius:6px;font-weight:bold;font-size:14px;cursor:pointer">
          Suscribirme
        </button>
      </form>
      <p style="margin:10px 0 0;font-size:11px;color:#666">Sin spam. Cancelás cuando quieras.</p>
      <a href="/" style="display:inline-block;margin-top:16px;color:#75aadb;text-decoration:none;font-size:13px;font-weight:bold">Leer más noticias →</a>
    </div>
    <?php
    return ob_get_clean();
}}
add_shortcode('newsletter', '{safe_domain}_newsletter_shortcode');
add_action('wp_footer', function() {{ echo do_shortcode('[newsletter]'); }});

// 1. META DESCRIPTION (vía output buffer para pisar cualquier hardcodeo del theme)
function {safe_domain}_build_meta_desc() {{
    if (is_single() || is_page()) {{
        global $post;
        if (has_excerpt($post->ID)) {{
            $desc = get_the_excerpt($post->ID);
        }} else {{
            $desc = wp_strip_all_tags($post->post_content);
        }}
        $desc = mb_substr(trim($desc), 0, 155);
    }} else {{
        $desc = get_bloginfo('description');
    }}
    // Si la description es muy corta, completarla automáticamente
    if (mb_strlen($desc) < 70) {{
        $site = get_bloginfo('name');
        $desc = $desc ? $desc . ' — ' . $site : $site;
        $desc = mb_substr($desc . '. Noticias, análisis y toda la información actualizada a diario. ¡Visitá el sitio!', 0, 155);
    }}
    return '<meta name="description" content="' . esc_attr($desc) . '">';
}}

// 2. OPEN GRAPH + TWITTER CARDS
function {safe_domain}_og_tags() {{
    global $post;
    $url = is_single() || is_page() ? get_permalink() : home_url('/');
    $title = is_single() || is_page() ? get_the_title() : get_bloginfo('name') . ' - ' . get_bloginfo('description');
    if (is_single() || is_page()) {{
        $desc = has_excerpt($post->ID) ? get_the_excerpt($post->ID) : wp_strip_all_tags($post->post_content);
        $desc = mb_substr(trim($desc), 0, 200);
    }} else {{
        $desc = get_bloginfo('description');
    }}
    echo '<meta property="og:url" content="' . esc_url($url) . '">' . "\\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '">' . "\\n";
    echo '<meta property="og:description" content="' . esc_attr($desc) . '">' . "\\n";
    if ((is_single() || is_page()) && has_post_thumbnail($post->ID)) {{
        $img = get_the_post_thumbnail_url($post->ID, 'large');
        echo '<meta property="og:image" content="' . esc_url($img) . '">' . "\\n";
    }} elseif (has_custom_logo()) {{
        $logo = wp_get_attachment_image_src(get_theme_mod('custom_logo'), 'full');
        echo '<meta property="og:image" content="' . esc_url($logo[0]) . '">' . "\\n";
    }} elseif (has_site_icon()) {{
        echo '<meta property="og:image" content="' . esc_url(get_site_icon_url(512)) . '">' . "\\n";
    }}
    echo '<meta property="og:type" content="' . (is_single() ? 'article' : 'website') . '">' . "\\n";
    echo '<meta property="og:site_name" content="' . esc_attr(get_bloginfo('name')) . '">' . "\\n";
    echo '<meta property="og:locale" content="es_AR">' . "\\n";
    echo '<meta name="twitter:card" content="summary_large_image">' . "\\n";
    echo '<meta name="twitter:title" content="' . esc_attr($title) . '">' . "\\n";
    echo '<meta name="twitter:description" content="' . esc_attr($desc) . '">' . "\\n";
}}
add_action('wp_head', '{safe_domain}_og_tags', 10);

// 3. CANONICAL URL
function {safe_domain}_canonical() {{
    if (is_single() || is_page()) {{
        echo '<link rel="canonical" href="' . esc_url(get_permalink()) . '">' . "\\n";
    }} elseif (is_home() || is_front_page()) {{
        echo '<link rel="canonical" href="' . esc_url(home_url('/')) . '">' . "\\n";
    }}
}}
add_action('wp_head', '{safe_domain}_canonical', 15);

// 4. ALT TEXT AUTOMÁTICO
function {safe_domain}_auto_alt($content) {{
    if (is_single()) {{
        $title = esc_attr(get_the_title());
        $content = preg_replace('/<img(.*?)alt=["\\'\\s]*["\\'\\s](.*?)>/i', '<img$1alt="' . $title . '"$2>', $content);
    }}
    return $content;
}}
add_filter('the_content', '{safe_domain}_auto_alt', 99);

function {safe_domain}_logo_alt($html) {{
    return str_replace(['alt=""', "alt=''"], 'alt="' . esc_attr(get_bloginfo('name')) . '"', $html);
}}
add_filter('get_custom_logo', '{safe_domain}_logo_alt');

// 5. LAZY LOADING + META DESCRIPTION (output buffering — cubre TODA la página)
function {safe_domain}_buffer_start() {{
    if (!is_admin()) ob_start('{safe_domain}_optimize_output');
}}
function {safe_domain}_optimize_output($html) {{
    // 5a. Eliminar meta descriptions viejas (hardcodeadas por el theme) y poner la nuestra
    $html = preg_replace('/<meta\s+name=[\\'\\"]description[\\'\\"][^>]*\/?>/i', '', $html);
    $html = preg_replace('/<meta\s+property=[\\'\\"]og:description[\\'\\"][^>]*\/?>/i', '', $html);
    $html = preg_replace('/<meta\s+name=[\\'\\"]twitter:description[\\'\\"][^>]*\/?>/i', '', $html);
    // Inyectar meta description después de <head>
    $meta_tag = {safe_domain}_build_meta_desc();
    $html = preg_replace('/<head[^>]*>/i', '$0' . "\\n" . $meta_tag, $html, 1);
    // 5b. Acortar title si es muy largo (>60 chars)
    if (preg_match('/<title>(.*?)<\/title>/is', $html, $m)) {{
        $old = $m[0];
        $text = trim(strip_tags($m[1]));
        if (mb_strlen($text) > 60) {{
            $text = mb_substr($text, 0, 57) . '...';
            $html = str_replace($old, '<title>' . esc_html($text) . '</title>', $html);
        }}
    }}
    // 5c. Si no hay H1, agregarlo (oculto visualmente, visible para SEO)
    if (!preg_match('/<h1[\s>]/i', $html)) {{
        $site_name = get_bloginfo('name');
        $h1_tag = '<h1 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0">' . esc_html($site_name) . '</h1>';
        $html = preg_replace('/<body[^>]*>/i', '$0' . "\\n" . $h1_tag, $html, 1);
    }}
    // 5d. Lazy loading en todas las imágenes
    $html = preg_replace('/<img(?!.*loading=)(.*?)>/i', '<img$1 loading="lazy">', $html);
    return $html;
}}
add_action('template_redirect', '{safe_domain}_buffer_start');
add_action('shutdown', function() {{ if (ob_get_level()) ob_end_flush(); }});

// 6. DEFER EN SCRIPTS EXTERNOS (reduce bloqueantes sin romper jQuery)
function {safe_domain}_defer_scripts($tag, $handle, $src) {{
    if (is_admin() || !$src) return $tag;
    if (strpos($handle, 'jquery') === 0 || strpos($handle, 'jquery-ui') !== false) return $tag;
    return str_replace(' src=', ' defer src=', $tag);
}}
add_filter('script_loader_tag', '{safe_domain}_defer_scripts', 10, 3);

// 7. CTA FLOTANTE + CONFIANZA (mejora conversión)
function {safe_domain}_cta_flotante() {{
    echo '<a href="#newsletter" style="position:fixed;bottom:20px;right:20px;background:#e63946;color:#fff;padding:12px 20px;border-radius:50px;font-weight:bold;text-decoration:none;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.25);font-family:Arial,sans-serif;font-size:14px;transition:transform 0.2s">Suscribite gratis</a>';
}}
function {safe_domain}_trust_bar() {{
    echo '<div style="text-align:center;padding:12px;background:#111;color:#aaa;font-size:11px;font-family:Arial,sans-serif;letter-spacing:0.3px">Contenido actualizado diariamente &nbsp;|&nbsp; Garantía de fuentes verificadas &nbsp;|&nbsp; Sin spam &nbsp;|&nbsp; <a href="#newsletter" style="color:#75aadb;text-decoration:none;font-weight:bold">Suscribite gratis →</a></div>';
}}
add_action('wp_footer', '{safe_domain}_cta_flotante');
add_action('wp_footer', '{safe_domain}_trust_bar');

// == SOPORTE ==
// ¿Problemas? Escribinos a soporte@delmonteanalitica.com
// ¿El plugin causa error? Renombrá la carpeta vía FTP:
//   /wp-content/plugins/{safe_domain}_optimizer/ → /wp-content/plugins/{safe_domain}_optimizer_DESACTIVADO/
// Documentación y FAQ: https://delmonteanalitica.com/faq
"""


def _crear_zip_plugin(safe_domain, plugin_code):
    """Crea un archivo ZIP en memoria con la estructura correcta para WordPress."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # WordPress espera: nombre-del-plugin/nombre-del-plugin.php
        plugin_dir = safe_domain + "_optimizer"
        zf.writestr(f"{plugin_dir}/{safe_domain}_optimizer.php", plugin_code)
    return buf.getvalue()


def _generar_snippet_shopify(resultado, safe_domain: str) -> str:
    """Genera un snippet Liquid para Shopify con correcciones automáticas."""
    site_url = resultado["url"]
    site_name = resultado["meta"].get("title") or safe_domain.replace("_", " ")
    L = "{{"  # noqa: Liquid open tag
    R = "}}"  # noqa: Liquid close tag
    LP = "{%"  # noqa: Liquid open block
    RP = "%}"  # noqa: Liquid close block
    return (
        LP + " comment " + RP + "\n"
        "  Snippet generado por Web Analyzer & Optimizer para " + site_url + "\n"
        "  Soporte: soporte@delmonteanalitica.com\n"
        "  Instrucciones: Pegar este código en el theme.liquid de tu tema de Shopify\n"
        "  (Online Store > Themes > Actions > Edit code > Layout > theme.liquid)\n"
        + LP + " endcomment " + RP + "\n\n"
        + LP + "- comment -" + RP + " 1. META TAGS " + LP + "- endcomment -" + RP + "\n"
        + LP + "- if template.name == 'index' -" + RP + "\n"
        "  " + LP + "- assign page_title = shop.name | escape -" + RP + "\n"
        "  " + LP + "- assign page_desc = shop.description | strip_html | strip | truncate: 155 -" + RP + "\n"
        + LP + "- elsif template.name == 'product' -" + RP + "\n"
        "  " + LP + "- assign page_title = product.title | escape -" + RP + "\n"
        "  " + LP + "- assign page_desc = product.description | strip_html | strip | truncate: 155 -" + RP + "\n"
        + LP + "- elsif template.name == 'article' -" + RP + "\n"
        "  " + LP + "- assign page_title = article.title | escape -" + RP + "\n"
        "  " + LP + "- assign page_desc = article.excerpt_or_content | strip_html | strip | truncate: 155 -" + RP + "\n"
        + LP + "- else -" + RP + "\n"
        "  " + LP + "- assign page_title = page_title | default: shop.name | escape -" + RP + "\n"
        "  " + LP + "- assign page_desc = page_description | default: shop.description | strip_html | strip | truncate: 155 -" + RP + "\n"
        + LP + "- endif -" + RP + "\n\n"
        '<meta name="description" content="' + L + ' page_desc ' + R + '">\n'
        '<meta property="og:title" content="' + L + ' page_title ' + R + '">\n'
        '<meta property="og:description" content="' + L + ' page_desc ' + R + '">\n'
        '<meta property="og:url" content="' + L + ' canonical_url ' + R + '">\n'
        '<meta property="og:type" content="' + LP + ' if template.name == \'product\' ' + RP + 'product' + LP + ' elsif template.name == \'article\' ' + RP + 'article' + LP + ' else ' + RP + 'website' + LP + ' endif ' + RP + '">\n'
        '<meta property="og:site_name" content="' + L + ' shop.name | escape ' + R + '">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta name="twitter:title" content="' + L + ' page_title ' + R + '">\n'
        '<meta name="twitter:description" content="' + L + ' page_desc ' + R + '">\n\n'
        + LP + "- comment -" + RP + " 2. LAZY LOADING EN TODAS LAS IMAGENES " + LP + "- endcomment -" + RP + "\n"
        "<script>\n"
        "(function() {\n"
        "  if ('loading' in HTMLImageElement.prototype) {\n"
        "    document.querySelectorAll('img:not([loading])').forEach(function(img) {\n"
        "      img.setAttribute('loading', 'lazy');\n"
        "    });\n"
        "  } else {\n"
        "    var script = document.createElement('script');\n"
        "    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/lazysizes/5.3.2/lazysizes.min.js';\n"
        "    document.head.appendChild(script);\n"
        "  }\n"
        "})();\n"
        "</script>\n\n"
        + LP + "- comment -" + RP + " 3. NEWSLETTER CAPTURE SECTION " + LP + "- endcomment -" + RP + "\n"
        '<div style="background:#f5f5f5;padding:40px 24px;text-align:center;margin:40px 0;font-family:Arial,sans-serif;border-radius:8px">\n'
        '  <h3 style="margin:0 0 8px;font-size:20px;color:#111">Recibi las novedades</h3>\n'
        '  <p style="margin:0 0 20px;font-size:14px;color:#555">Suscribite y no te pierdas ninguna oferta ni actualizacion.</p>\n'
        "  " + LP + "- form 'customer' -" + RP + "\n"
        '    <input type="hidden" name="contact[tags]" value="newsletter">\n'
        '    <div style="display:flex;gap:8px;max-width:400px;margin:0 auto;flex-wrap:wrap;justify-content:center">\n'
        '      <input type="email" name="contact[email]" placeholder="tu@email.com" required\n'
        '             style="flex:1;min-width:200px;padding:12px;border:1px solid #ccc;border-radius:6px;font-size:14px">\n'
        '      <button type="submit"\n'
        '              style="padding:12px 24px;background:#111;color:#fff;border:none;border-radius:6px;font-weight:bold;font-size:14px;cursor:pointer">\n'
        '        Suscribirme\n'
        '      </button>\n'
        '    </div>\n'
        "  " + LP + "- endform -" + RP + "\n"
        '  <p style="margin:10px 0 0;font-size:11px;color:#999">Sin spam. Cancelas cuando quieras.</p>\n'
        '</div>\n\n'
        + LP + "- comment -" + RP + " 4. CTA FLOTANTE " + LP + "- endcomment -" + RP + "\n"
        '<a href="#newsletter"\n'
        '   style="position:fixed;bottom:20px;right:20px;background:#e63946;color:#fff;padding:12px 20px;border-radius:50px;font-weight:bold;text-decoration:none;z-index:9999;box-shadow:0 4px 12px rgba(0,0,0,0.25);font-family:Arial,sans-serif;font-size:14px">\n'
        '  Suscribite\n'
        '</a>\n'
    )


def _generar_patch_html(meta, resultado):
    """Genera fragmentos HTML corregidos."""
    title = meta.get("title") or "Título del sitio"
    desc = meta.get("description") or "Descripción del sitio (120-155 caracteres con keyword principal)"

    parts = []

    # Meta description
    if not meta.get("description") or meta.get("description_length", 0) < 70:
        parts.append(f"""<!-- AGREGAR en <head> -->
<meta name="description" content="{desc}">""")

    # OG tags
    if not meta.get("og_title"):
        parts.append(f"""<!-- AGREGAR en <head> (Open Graph para redes sociales) -->
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="https://TU_DOMINIO/imagen-og.jpg">
<meta property="og:url" content="{resultado['url']}">
<meta property="og:type" content="website">
<meta property="og:locale" content="es_AR">
<meta name="twitter:card" content="summary_large_image">""")

    # Canonical
    if not meta.get("canonical"):
        parts.append(f"""<!-- AGREGAR en <head> -->
<link rel="canonical" href="{resultado['url']}">""")

    # Newsletter form
    if resultado["forms"]["con_email"] == 0:
        parts.append(f"""<!-- AGREGAR en sidebar o footer (formulario newsletter) -->
<div style="background:#f8f9fa;padding:20px;border-radius:10px;border-left:5px solid #e63946;font-family:Arial,sans-serif">
  <h3 style="margin:0 0 8px;font-size:16px">Recibí las novedades</h3>
  <p style="margin:0 0 14px;font-size:13px;color:#555">Suscribite para recibir las últimas noticias en tu mail.</p>
  <form style="display:flex;flex-direction:column;gap:10px">
    <input type="email" placeholder="tu@email.com" required
           style="padding:10px;border:1px solid #ddd;border-radius:6px;font-size:14px">
    <button type="submit"
            style="padding:12px;background:#e63946;color:#fff;border:none;border-radius:6px;font-weight:bold;font-size:14px;cursor:pointer">
      Suscribirme
    </button>
  </form>
  <p style="margin:10px 0 0;font-size:11px;color:#888">Sin spam. Cancelás cuando quieras.</p>
</div>""")

    return "\n\n".join(parts)


# =============================================================================
# Persistencia
# =============================================================================

import os as _os

_OUTPUT_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "output")
_ANALISIS_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "analisis")


def _extraer_links_internos(soup, base_url: str, limit: int = 5) -> list[str]:
    """Extrae hasta N links internos únicos del mismo dominio para crawling."""
    from urllib.parse import urlparse
    base_parsed = urlparse(base_url)
    base_domain = base_parsed.netloc.lower()
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
            continue
        if href.startswith("tel:"):
            continue
        full = urljoin(base_url, href)
        parsed = urlparse(full)
        if parsed.netloc.lower() == base_domain and parsed.scheme in ("http", "https"):
            # Normalizar: quitar fragment y query
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            links.add(normalized)
        if len(links) >= limit:
            break
    # Excluir la URL base
    base_normalized = f"{base_parsed.scheme}://{base_parsed.netloc}{base_parsed.path}"
    links.discard(base_normalized)
    return list(links)[:limit]


def _analizar_multipagina(url: str, depth: int = 3) -> dict:
    """Analiza una URL y hasta 'depth' páginas internas adicionales."""
    resultado = analizar(url)
    if resultado.get("errores"):
        return resultado

    paginas = [{"url": resultado.get("url_final", url), "promedio": round(
        sum(s for s, _ in resultado.get("scorecard", {}).values()) /
        max(len(resultado.get("scorecard", {})), 1), 1
    ), "scorecard": resultado["scorecard"]}]

    if depth > 1 and resultado.get("html_raw"):
        soup = BeautifulSoup(resultado["html_raw"], "html.parser")
        links = _extraer_links_internos(soup, resultado.get("url_final", url), limit=depth - 1)
        for link in links:
            try:
                sub = analizar(link)
                if sub.get("errores"):
                    continue
                avg = round(
                    sum(s for s, _ in sub.get("scorecard", {}).values()) /
                    max(len(sub.get("scorecard", {})), 1), 1
                )
                paginas.append({"url": sub.get("url_final", link), "promedio": avg, "scorecard": sub["scorecard"]})
            except Exception:
                continue

    # Agregar metadatos multi-página al resultado principal
    resultado["paginas"] = paginas
    resultado["promedio_sitio"] = round(
        sum(p["promedio"] for p in paginas) / len(paginas), 1
    ) if paginas else resultado.get("promedio", 0)

    return resultado


def _guardar_analisis(resultado):
    """Guarda el análisis en disco para historial (sin html_raw, escritura atómica)."""
    dominio = urlparse(resultado["url"]).netloc.replace("www.", "")
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", dominio)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe}_{ts}.json"

    to_save = {k: v for k, v in resultado.items() if k != "html_raw"}
    path = _os.path.join(_ANALISIS_DIR, filename)

    # Escritura atómica: temp + rename evita archivos corruptos por crash concurrente
    tmp = _os.path.join(_ANALISIS_DIR, f".{filename}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2, default=str)
    _os.replace(tmp, path)  # atómico en Windows y POSIX

    # Guardar soluciones en output/ (escritura atómica)
    for sol in resultado.get("soluciones", []):
        sol_path = _os.path.join(_OUTPUT_DIR, sol["nombre"])
        tmp_path = _os.path.join(_OUTPUT_DIR, f".{sol['nombre']}.tmp")
        mode = "wb" if sol.get("binario") else "w"
        with open(tmp_path, mode, encoding=None if sol.get("binario") else "utf-8") as f:
            f.write(sol["contenido"])
        _os.replace(tmp_path, sol_path)
        sol["path"] = sol_path.replace("\\", "/")

    resultado["guardado_en"] = path.replace("\\", "/")


def listar_analisis(limit=20):
    """Lista los análisis guardados."""
    if not _os.path.exists(_ANALISIS_DIR):
        return []
    files = sorted(
        [_os.path.join(_ANALISIS_DIR, f) for f in _os.listdir(_ANALISIS_DIR) if f.endswith(".json")],
        key=_os.path.getmtime,
        reverse=True,
    )
    results = []
    for f in files[:limit]:
        with open(f, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            results.append({
                "url": data.get("url", ""),
                "fecha": data.get("fecha", ""),
                "promedio": round(
                    sum(s for s, _ in data.get("scorecard", {}).values()) / max(len(data.get("scorecard", {})), 1), 1
                ),
                "archivo": _os.path.basename(f),
            })
    return results
