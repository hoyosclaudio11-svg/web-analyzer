import requests, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

r = requests.get('http://revista-espectaculos.com.ar/', headers={'User-Agent': 'Mozilla/5.0'})
html = r.text

# Buscar elementos de navegacion reales (no CSS)
print("=== BUSCANDO ELEMENTOS NAV ===")
for tag in ['<nav', 'wp-block-navigation__container', 'wp-block-page-list', 'class="wp-block-navigation"', 'menu-item', 'page_item']:
    idx = html.find(tag)
    if idx >= 0:
        print(f"  ENCONTRADO '{tag}' en pos {idx}")
        print(f"    Contexto: ...{html[idx:idx+200]}...")
    else:
        print(f"  NO: '{tag}'")

# Buscar links de navegacion
print("\n=== BUSCANDO NAV LINKS ===")
import re
links = re.findall(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>([^<]*)</a>', html)
nav_links = []
for href, text in links:
    text = text.strip()
    if text and len(text) < 50:
        nav_links.append((href, text))

# Mostrar los primeros 30 links
for href, text in nav_links[:30]:
    print(f"  '{text}' -> {href}")

# Buscar estructura del header
print("\n=== HEADER ===")
header_idx = html.find('<header')
if header_idx >= 0:
    header_end = html.find('</header>', header_idx)
    if header_end >= 0:
        header_html = html[header_idx:header_end+9]
        print(header_html[:1500])
