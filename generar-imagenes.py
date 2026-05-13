"""Genera imágenes para redes sociales de Web Analyzer."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(__file__), "social-images")
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1080
BG = (13, 17, 23)
BG2 = (22, 27, 34)
BORDER = (48, 54, 61)
TEXT = (230, 237, 243)
TEXT2 = (139, 148, 158)
TEXT3 = (110, 118, 129)
BLUE = (88, 166, 255)
GREEN = (63, 185, 80)
YELLOW = (210, 153, 34)
RED = (248, 81, 73)
ACCENT = (31, 111, 235)

FONT_BOLD = None
FONT_REGULAR = None
FONT_TITLE = None

for path in [
    "C:\\Windows\\Fonts\\segoeuib.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]:
    if os.path.exists(path) and not FONT_BOLD:
        FONT_BOLD = path
    elif os.path.exists(path) and not FONT_REGULAR:
        FONT_REGULAR = path

if not FONT_BOLD:
    FONT_BOLD = FONT_REGULAR = "arial.ttf"


def load_font(size, bold=True):
    path = FONT_BOLD if bold else (FONT_REGULAR or FONT_BOLD)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def texto_centrado(draw, texto, y, font, color):
    bbox = draw.textbbox((0, 0), texto, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) / 2, y), texto, fill=color, font=font)


def texto(draw, texto, x, y, font, color):
    draw.text((x, y), texto, fill=color, font=font)


def color_score(s):
    if s >= 8:
        return GREEN
    if s >= 5:
        return YELLOW
    return RED


def hacer_scorecard(sitio, label, promedio, scores, filename):
    """Crea imagen de scorecard para un sitio."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo sutil
    draw.rectangle([40, 40, W - 40, H - 40], outline=BORDER, width=2)

    # Header
    texto_centrado(draw, "Web Analyzer", 80, load_font(28, True), BLUE)
    texto_centrado(draw, "Auditoría de sitio web", 120, load_font(16, False), TEXT3)

    # Promedio grande
    color_prom = color_score(promedio)
    texto_centrado(draw, str(promedio), 200, load_font(120, True), color_prom)
    texto_centrado(draw, "/ 10", 300, load_font(24, False), TEXT3)

    # Sitio
    texto_centrado(draw, sitio, 380, load_font(36, True), BLUE)
    texto_centrado(draw, label, 425, load_font(18, False), TEXT3)

    # Scorecards — 5 columnas
    cats = list(scores.keys())
    col_w = (W - 160) / 5
    for i, cat in enumerate(cats):
        x = 80 + i * col_w + col_w / 2
        s = scores[cat]
        c = color_score(s)

        # Fondo card
        cx = 80 + i * col_w
        draw.rectangle([cx, 500, cx + col_w - 10, 720], outline=BORDER, width=1)

        # Nombre categoría
        texto_centrado(draw, cat, 530, load_font(14, True), TEXT2)
        # Puntaje
        texto_centrado(draw, str(s), 580, load_font(56, True), c)
        texto_centrado(draw, "/10", 640, load_font(14, False), TEXT3)

    # Footer
    texto_centrado(draw, "Analizá tu sitio gratis en 30 segundos", 800, load_font(20, False), TEXT2)
    texto_centrado(draw, "web-analyzer-1-l8uc.onrender.com", 840, load_font(16, False), BLUE)

    # Marca de agua sutíl
    texto_centrado(draw, "web-analyzer", H - 80, load_font(12, False), TEXT3)

    img.save(os.path.join(OUT, filename))
    print(f"  [OK] {filename}")


def hacer_antes_despues(sitio, antes, despues, mejoras, filename):
    """Crea imagen de antes/después."""
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    texto_centrado(draw, "Web Analyzer", 60, load_font(28, True), BLUE)
    texto_centrado(draw, "Antes y Después", 100, load_font(18, False), TEXT3)

    texto_centrado(draw, sitio, 180, load_font(32, True), BLUE)

    # Antes - Después con flecha
    texto_centrado(draw, "ANTES", 270, load_font(18, True), RED)
    texto_centrado(draw, str(antes), 310, load_font(96, True), RED)
    texto_centrado(draw, "/ 10", 390, load_font(20, False), TEXT3)

    texto_centrado(draw, "→", 470, load_font(48, True), TEXT2)

    texto_centrado(draw, "DESPUÉS", 540, load_font(18, True), GREEN)
    texto_centrado(draw, str(despues), 580, load_font(96, True), GREEN)
    texto_centrado(draw, "/ 10", 660, load_font(20, False), TEXT3)

    # Mejoras aplicadas
    texto_centrado(draw, "Soluciones aplicadas:", 740, load_font(16, False), TEXT2)
    pills = "  ·  ".join(mejoras)
    texto_centrado(draw, pills, 775, load_font(15, False), TEXT3)

    # CTA
    draw.rectangle([W / 2 - 160, 850, W / 2 + 160, 910], outline=ACCENT, width=2)
    texto_centrado(draw, "Analizar mi sitio gratis →", 865, load_font(18, True), BLUE)

    img.save(os.path.join(OUT, filename))
    print(f"  [OK] {filename}")


# =====================================================
# Generar todas las imágenes
# =====================================================
print("Generando imágenes para redes...")

# Scorecards sitios famosos
hacer_scorecard(
    "cariverplate.com.ar", "River Plate — Sitio Oficial",
    3.2,
    {"SEO": 1, "Acces.": 2, "Rend.": 3, "Conv.": 4, "UX": 6},
    "1-river.png",
)

hacer_scorecard(
    "one-piece.com", "One Piece — Sitio Oficial (Japón)",
    4.0,
    {"SEO": 5, "Acces.": 2, "Rend.": 5, "Conv.": 4, "UX": 4},
    "2-onepiece.png",
)

hacer_scorecard(
    "yahoo.com", "Yahoo — Portal #1 USA",
    4.8,
    {"SEO": 4, "Acces.": 3, "Rend.": 6, "Conv.": 4, "UX": 7},
    "3-yahoo.png",
)

hacer_scorecard(
    "bocajuniors.com.ar", "Boca Juniors — Sitio Oficial",
    6.0,
    {"SEO": 7, "Acces.": 4, "Rend.": 4, "Conv.": 5, "UX": 10},
    "4-boca.png",
)

hacer_scorecard(
    "ole.com.ar", "Diario Deportivo Olé",
    6.6,
    {"SEO": 6, "Acces.": 6, "Rend.": 7, "Conv.": 5, "UX": 9},
    "5-ole.png",
)

# Antes y Después — WordPress
hacer_antes_despues(
    "riverplate-info.com.ar", 5.5, 9.6,
    ["lazy loading", "meta tags", "WebP", "alt text"],
    "ba-riverplate.png",
)

hacer_antes_despues(
    "diario-albiceleste.com.ar", 5.8, 9.6,
    ["lazy loading", "OG tags", "WebP", "formularios"],
    "ba-albiceleste.png",
)

hacer_antes_despues(
    "revista-espectaculos.com.ar", 6.0, 9.6,
    ["lazy loading", "SEO", "WebP", "CTAs"],
    "ba-espectaculos.png",
)

print(f"\n[OK] {len(os.listdir(OUT))} imagenes generadas en {OUT}")
