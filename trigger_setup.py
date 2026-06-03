"""Disparar setup via admin_init — visit wp-admin."""
import requests

# Simular una visita al admin para disparar admin_init
# No necesitamos loguearnos - el hook corre antes de cualquier verificacion de auth
# Pero si el setup da error, el admin tambien dara 500

try:
    r = requests.get("https://riverplate-info.com.ar/wp-admin/", timeout=30, allow_redirects=True)
    print(f"Status: {r.status_code}")
    print(f"URL final: {r.url}")
    print(f"Length: {len(r.text)}")
    if r.status_code == 500:
        print("ERROR 500 en admin - el setup fallo")
        print(r.text[:1000])
    elif r.status_code == 200:
        print("Admin cargo OK - setup deberia haber corrido")
        # Check if redirected to login (normal)
        if "wp-login" in r.url or "log" in r.text.lower():
            print("Redirigio a login (normal)")
except Exception as e:
    print(f"Error: {e}")

# Verificar el frontend de nuevo
print("\n=== Verificando frontend post-setup ===")
r2 = requests.get("https://riverplate-info.com.ar", timeout=30)
print(f"Status: {r2.status_code}")
print(f"Length: {len(r2.text)}")
# Buscar elementos de setup
for term in ["Inicio", "Plantilla", "Calendario", "Noticias", "Tienda", "Contacto"]:
    count = r2.text.count(term)
    print(f"  '{term}': {count}")
