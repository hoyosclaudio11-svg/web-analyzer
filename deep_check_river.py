"""Analisis profundo del HTML de River Plate Info."""
import requests, re

r = requests.get("https://riverplate-info.com.ar", timeout=30)
html = r.text
print(f"Status: {r.status_code}, Length: {len(html)}")

# 1. MU-plugin CSS presente?
print("\n=== CSS ===")
print(f"wa-river-club-theme: {html.count('wa-river-club-theme')}")
print(f"wa-river-club.php: {html.count('wa-river-club')}")

# 2. Que hojas de estilo se cargan?
print("\n=== STYLESHEETS CARGADOS ===")
styles = re.findall(r"<link[^>]*rel=['\"]stylesheet['\"][^>]*href=['\"]([^'\"]+)['\"][^>]*>", html)
for s in styles[:20]:
    name = s.split('/')[-1].split('?')[0]
    print(f"  {name}")
    if 'newsup' in s.lower() or 'newstack' in s.lower():
        print(f"    ^^^ ESTE DEBERIA SER DEQUEUEADO")

# 3. Menu de navegacion
print("\n=== NAV (buscando menu principal) ===")
# Buscar clases de nav del tema
nav_areas = re.findall(r'<nav[^>]*class=["\']([^"\']*)["\']', html)
for n in nav_areas:
    print(f"  Nav class: {n}")

# Buscar menu items en header/parte superior
menus = re.findall(r'(?:menu-item|nav-item|nav-link)[^>]*>([^<]*)<', html)
print(f"\n=== MENU ITEMS ENCONTRADOS ===")
for m in menus[:20]:
    if m.strip():
        print(f"  {m.strip()}")

# 4. Logo
print("\n=== LOGO ===")
logo_imgs = re.findall(r'<img[^>]*class=["\']([^"\']*custom-logo[^"\']*)["\'][^>]*src=["\']([^"\']+)["\']', html)
for cls, src in logo_imgs:
    print(f"  {cls}: {src}")

# 5. Header completo
print("\n=== HEADER HTML (primeros 1000 chars) ===")
header = re.search(r'<header[^>]*>(.*?)</header>', html, re.DOTALL)
if header:
    print(header.group(1)[:1000])
else:
    # Buscar mg-headwidget
    hw = re.search(r'<div[^>]*class=["\'][^"\']*mg-headwidget[^"\']*["\'](.*?)</div>', html, re.DOTALL)
    if hw:
        print(hw.group(0)[:1000])
    else:
        print("No se encontro header ni mg-headwidget")

# 6. Ver clasess del body
print("\n=== BODY CLASSES ===")
body = re.search(r'<body[^>]*class=["\']([^"\']*)["\']', html)
if body:
    print(body.group(1))

# 7. Hero
print(f"\n=== HERO ===")
print(f"river-hero: {html.count('river-hero')}")
print(f"wp-block-cover: {html.count('wp-block-cover')}")
hero = re.search(r'river-hero(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
if hero:
    print(hero.group(0)[:400])

# 8. Newsletter duplicados
print(f"\n=== NEWSLETTER ===")
print(f"newsletter forms: {html.count('newsletter')}")
print(f"subscribe: {html.count('subscribe')}")
