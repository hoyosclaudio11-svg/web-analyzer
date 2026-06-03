"""Generar y subir imagenes para el carrusel."""
import os
import requests, base64
from pathlib import Path
from PIL import Image, ImageDraw

WP_USER = "a0110133"
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()

def crear_imagen(domain, score, label, color_bg, filename):
    img = Image.new("RGB", (600, 340), "#21262d")
    draw = ImageDraw.Draw(img)

    for i in range(10):
        y = i * 34
        shade = 33 + i * 2
        hex_color = f"#{shade:02x}{shade+3:02x}{shade+6:02x}"
        draw.rectangle([0, y, 600, y + 34], fill=hex_color)

    draw.rectangle([20, 20, 580, 44], fill="#0d1117", outline="#30363d")
    draw.rectangle([30, 28, 570, 36], fill="#161b22")
    draw.text((40, 18), domain, fill="#58a6ff")

    cx, cy = 540, 80
    r = 32
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color_bg)

    score_str = str(score)
    bbox = draw.textbbox((0, 0), score_str)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw/2, cy - th/2), score_str, fill="#000000")

    draw.text((40, 70), label, fill="#8b949e")

    categories = [
        ("SEO", 2, "#f85149"), ("Acces.", 3, "#f85149"),
        ("Rend.", 1, "#f85149"), ("Conv.", 4, "#f85149"), ("UX", 5, "#d29922"),
    ]
    y_start = 120
    for cat_name, cat_score, cat_color in categories:
        bar_width = cat_score * 28
        draw.text((40, y_start), cat_name, fill="#8b949e")
        draw.rectangle([110, y_start + 4, 110 + bar_width, y_start + 16], fill=cat_color)
        draw.text((114 + bar_width, y_start), str(cat_score), fill=cat_color)
        y_start += 26

    draw.text((40, 290), "Analizar ahora ->", fill="#58a6ff")

    out_path = Path(f"E:/DelMonte/web-analyzer/{filename}")
    img.save(out_path, "PNG")
    print(f"  {filename} guardada")
    return out_path

print("=== Generando imagenes ===")
sitios = [
    ("cariverplate.com.ar", 3.2, "River Plate - Sitio Oficial", "#f85149", "img-river.png"),
    ("one-piece.com", 4.0, "One Piece - Oficial Japon", "#f85149", "img-onepiece.png"),
    ("yahoo.com", 4.8, "Yahoo - Portal #1 USA", "#f85149", "img-yahoo.png"),
    ("bocajuniors.com.ar", 6.0, "Boca Juniors - Oficial", "#d29922", "img-boca.png"),
    ("ole.com.ar", 6.6, "Diario Deportivo Ole", "#d29922", "img-ole.png"),
]

for domain, score, label, color, fname in sitios:
    crear_imagen(domain, score, label, color, fname)

print("\n=== Subiendo imagenes a WP ===")
for domain, score, label, color, fname in sitios:
    path = Path(f"E:/DelMonte/web-analyzer/{fname}")
    with open(path, "rb") as f:
        img_data = f.read()

    img_headers = {
        'Authorization': f'Basic {auth}',
        'Content-Type': 'image/png',
        'Content-Disposition': f'attachment; filename="{fname}"'
    }
    r = requests.post(f'{BASE}/media', headers=img_headers, data=img_data)
    if r.status_code == 201:
        j = r.json()
        print(f"  {fname}: ID={j['id']} URL={j['source_url']}")
    else:
        print(f"  {fname}: ERROR {r.status_code} {r.text[:150]}")

print("\n=== LISTO ===")
