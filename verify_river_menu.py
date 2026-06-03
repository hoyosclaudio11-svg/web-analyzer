import requests, re
r = requests.get("https://riverplate-info.com.ar", timeout=30)
html = r.text

# Buscar menu items en HTML
print("=== MENU ITEMS (hrefs con paginas) ===")
menu_links = re.findall(r'<a[^>]*href="https://riverplate-info\.com\.ar/([^"]*)"[^>]*>(.*?)</a>', html)
seen = set()
for href, text in menu_links:
    href_clean = href.rstrip('/')
    if href_clean in ['inicio','plantilla','calendario','noticias','tienda','contacto'] and href_clean not in seen:
        seen.add(href_clean)
        print(f"  /{href_clean} -> {text.strip()}")

# Buscar home page
print(f"\n=== HOME PAGE ===")
print(f"show_on_front mencionado: {'page_on_front' in html or 'Inicio' in html}")

# Buscar el hero
print(f"\n=== HERO ===")
print(f"river-hero: {html.count('river-hero')}")
print(f"Bienvenido: {html.count('Bienvenido')}")
print(f"EL MONUMENTAL: {html.count('EL MONUMENTAL')}")

# Buscar logo
print(f"\n=== LOGO ===")
print(f"custom-logo: {html.count('custom-logo')}")
print(f"logo image: {html.count('river-logo')}")

# SportsPress
print(f"\n=== SPORTSPRESS ===")
print(f"sp-template: {html.count('sp-template')}")
print(f"sp-data-table: {html.count('sp-data-table')}")

# Check menu structure in nav
nav_match = re.search(r'<nav[^>]*>(.*?)</nav>', html, re.DOTALL)
if nav_match:
    print(f"\n=== NAV HTML (primeros 500 chars) ===")
    print(nav_match.group(1)[:500])
