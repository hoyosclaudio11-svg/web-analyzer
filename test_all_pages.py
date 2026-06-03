import requests, re

pages = [
    ("Inicio", "https://riverplate-info.com.ar/"),
    ("Plantilla", "https://riverplate-info.com.ar/plantilla/"),
    ("Calendario", "https://riverplate-info.com.ar/calendario/"),
    ("Noticias", "https://riverplate-info.com.ar/noticias/"),
    ("Tienda", "https://riverplate-info.com.ar/tienda/"),
    ("Contacto", "https://riverplate-info.com.ar/contacto/"),
]

for name, url in pages:
    try:
        r = requests.get(url, timeout=30)
        theme_css = len(re.findall(r'https?://[^"<>\s]*themes[^"<>\s]*\.css[^"<>\s]*', r.text))
        our_css = r.text.count("wa-river-club-theme")
        menu_count = r.text.count("menu-item")
        hero = r.text.count("Bienvenido")
        print(f"{name:12} | Status:{r.status_code} | Length:{len(r.text):6} | OurCSS:{our_css} | ThemeCSS:{theme_css} | Menu:{menu_count}")
    except Exception as e:
        print(f"{name:12} | ERROR: {e}")
