import requests, re
r = requests.get("https://riverplate-info.com.ar", timeout=30)
html = r.text

# Buscar todos los <link> de stylesheet con sus URLs completas
print("=== TODOS LOS STYLESHEETS ===")
links = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*>', html)
for link in links:
    href = re.search(r'href=["\']([^"\']+)["\']', link)
    id_attr = re.search(r'id=["\']([^"\']+)-css["\']', link)
    if href:
        url = href.group(1)
        lid = id_attr.group(1) if id_attr else "?"
        print(f"  [{lid}] {url}")

# Ver el orden: los CSS de tema estan inline o en <link>?
print("\n=== CSS INLINE (primeros 200 chars de cada style) ===")
inlines = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
for i, css in enumerate(inlines):
    preview = css.strip()[:150].replace('\n',' ')
    print(f"  Style #{i+1}: {preview}...")

# Verificar si hay CSS de tema hardcodeado en header.php
print("\n=== BUSCANDO /themes/ EN HEAD ===")
head = re.search(r'<head>(.*?)</head>', html, re.DOTALL)
if head:
    head_content = head.group(1)
    theme_refs = re.findall(r'[^"]*themes[^"]*', head_content)
    for t in theme_refs:
        print(f"  {t}")
