"""
LIMPIEZA + PAGINA DE PRECIOS — webanalyzer.com.ar/web/
1. Elimina todos los posts del blog fantasma
2. Elimina la pagina "Blog"
3. Crea pagina "Precios" profesional
"""
import requests, base64, json, time

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

POSTS_TO_DELETE = [1, 34, 40, 49, 61]  # todos los posts del blog
BLOG_PAGE_ID = 31

# ---------------------------------------------------------------------------
# 1. Eliminar posts
# ---------------------------------------------------------------------------
print("1. Eliminando posts del blog fantasma...")
for pid in POSTS_TO_DELETE:
    r = requests.delete(f'{BASE}/posts/{pid}?force=true', headers=headers)
    if r.status_code in (200, 201):
        print(f"   Post ID={pid} ELIMINADO")
    else:
        print(f"   Post ID={pid} ERROR {r.status_code}: {r.text[:100]}")

# ---------------------------------------------------------------------------
# 2. Eliminar pagina "Blog"
# ---------------------------------------------------------------------------
print("\n2. Eliminando pagina 'Blog'...")
r = requests.delete(f'{BASE}/pages/{BLOG_PAGE_ID}?force=true', headers=headers)
if r.status_code in (200, 201):
    print(f"   Pagina Blog (ID={BLOG_PAGE_ID}) ELIMINADA")
else:
    print(f"   ERROR {r.status_code}: {r.text[:100]}")

# ---------------------------------------------------------------------------
# 3. Quitar page_for_posts de settings
# ---------------------------------------------------------------------------
print("\n3. Configurando settings (sin blog)...")
r = requests.post(f'{BASE}/settings', headers=headers, json={'page_for_posts': 0})
if r.status_code in (200, 201):
    print("   page_for_posts=0 OK")
else:
    print(f"   ERROR {r.status_code}: {r.text[:100]}")

# ---------------------------------------------------------------------------
# 4. Crear pagina "Precios"
# ---------------------------------------------------------------------------
print("\n4. Creando pagina 'Precios'...")

PRICING_HTML = """
import os<h2 style="text-align:center;font-size:2rem;margin-bottom:8px">Planes simples, sin vueltas</h2>
<p style="text-align:center;color:#aaa;font-size:1.05rem;margin-bottom:48px">Un solo pago. Sin suscripciones. Sin letra chica.</p>

<div style="display:flex;gap:24px;justify-content:center;flex-wrap:wrap;max-width:900px;margin:0 auto">

<!-- GRATIS -->
<div style="flex:1;min-width:260px;max-width:400px;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px 24px;text-align:center">
  <h3 style="color:#fff;font-size:1.3rem;margin:0 0 8px">Gratis</h3>
  <p style="color:#8b949e;font-size:0.9rem;margin:0 0 20px">Diagnóstico instantáneo</p>
  <div style="font-size:2.5rem;font-weight:700;color:#58a6ff;margin-bottom:20px">$0</div>
  <ul style="list-style:none;padding:0;text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:2">
    <li>✅ Scorecard 0-10 en 5 categorías</li>
    <li>✅ Hallazgos críticos detectados</li>
    <li>✅ Tecnología del sitio identificada</li>
    <li>✅ Link público compartible</li>
    <li>❌ Soluciones descargables</li>
    <li>❌ Plugin WordPress .zip</li>
    <li>❌ Reporte JSON completo</li>
  </ul>
  <a href="https://web-analyzer-1-l8uc.onrender.com/" style="display:block;margin-top:24px;padding:12px;background:#30363d;color:#c9d1d9;border-radius:8px;text-decoration:none;font-weight:600">Analizar gratis →</a>
</div>

<!-- PAGO UNICO -->
<div style="flex:1;min-width:260px;max-width:400px;background:#161b22;border:2px solid #1f6feb;border-radius:12px;padding:32px 24px;text-align:center;position:relative">
  <div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#1f6feb;color:#fff;padding:4px 16px;border-radius:20px;font-size:0.8rem;font-weight:600">RECOMENDADO</div>
  <h3 style="color:#fff;font-size:1.3rem;margin:0 0 8px">Análisis completo</h3>
  <p style="color:#8b949e;font-size:0.9rem;margin:0 0 20px">Diagnóstico + soluciones</p>
  <div style="font-size:2.5rem;font-weight:700;color:#fff;margin-bottom:4px">ARS 12.000</div>
  <div style="color:#8b949e;font-size:0.8rem;margin-bottom:20px">Pago único — No se renueva</div>
  <ul style="list-style:none;padding:0;text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:2">
    <li>✅ Todo lo del plan Gratis</li>
    <li>✅ Plugin WordPress .zip listo para instalar</li>
    <li>✅ Correcciones automáticas (SEO, lazy loading, OG tags, CTAs)</li>
    <li>✅ Reporte JSON descargable</li>
    <li>✅ Soluciones paso a paso por categoría</li>
    <li>✅ Acceso al historial de análisis</li>
    <li>✅ Soporte por email</li>
  </ul>
  <a href="https://web-analyzer-1-l8uc.onrender.com/" style="display:block;margin-top:24px;padding:12px;background:#1f6feb;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.05rem">Analizar y comprar →</a>
</div>

</div>

<div style="max-width:700px;margin:48px auto 0;text-align:center;color:#8b949e;font-size:0.9rem;line-height:1.8">

<h3 style="color:#fff;font-size:1.2rem;margin-bottom:16px">¿Por qué un pago único?</h3>

<p>Una auditoría profesional con una agencia cuesta entre <strong style="color:#fff">$50.000 y $200.000 ARS</strong>. Web Analyzer te da el mismo nivel de detalle por <strong style="color:#58a6ff">$12.000 ARS</strong>, en 30 segundos, sin esperar turno.</p>

<p style="margin-top:20px"><strong style="color:#fff">Sin suscripción. Sin cuotas escondidas.</strong> Pagás una vez, descargás tu plugin, y es tuyo para siempre.</p>

</div>

<div style="max-width:700px;margin:40px auto 0;padding:24px;background:#161b22;border:1px solid #30363d;border-radius:12px;text-align:center">

<h3 style="color:#fff;font-size:1.1rem;margin:0 0 12px">Garantía de 7 días</h3>

<p style="color:#8b949e;font-size:0.9rem;margin:0">Si después de aplicar las soluciones tu sitio no mejora al menos <strong style="color:#fff">una categoría</strong> del scorecard, te devolvemos el 100% del dinero. Sin preguntas.</p>

</div>

<div style="max-width:700px;margin:40px auto 0;text-align:center">

<h3 style="color:#fff;font-size:1.2rem;margin-bottom:16px">Preguntas frecuentes</h3>

<div style="text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:1.7">

<p><strong style="color:#fff">¿Necesito saber de programación?</strong><br>No. El plugin se instala como cualquier plugin de WordPress. Un clic, activar, y las correcciones se aplican solas.</p>

<p><strong style="color:#fff">¿Funciona en sitios que no son WordPress?</strong><br>El análisis funciona en cualquier URL pública. Las soluciones descargables incluyen un archivo HTML con correcciones manuales y un JSON con todos los datos para que tu desarrollador los implemente.</p>

<p><strong style="color:#fff">¿Cuántos análisis incluye el pago?</strong><br>Un análisis completo por URL. Si necesitás analizar varios sitios, cada uno requiere su compra individual.</p>

<p><strong style="color:#fff">¿Qué formas de pago aceptan?</strong><br>MercadoPago: tarjeta de crédito, débito, transferencia, y efectivo en puntos de pago.</p>

<p><strong style="color:#fff">¿Cuánto tarda el análisis?</strong><br>Menos de 30 segundos. Procesamos tu URL en tiempo real y ves los resultados instantáneamente.</p>

</div>

</div>"""

payload = {
    'title': 'Precios',
    'slug': 'precios',
    'content': PRICING_HTML,
    'status': 'publish',
}
r = requests.post(f'{BASE}/pages', headers=headers, json=payload)
if r.status_code in (200, 201):
    data = r.json()
    print(f"   Pagina 'Precios' CREADA — ID={data['id']} slug={data['slug']}")
    print(f"   URL: https://webanalyzer.com.ar/web/precios/")
else:
    print(f"   ERROR {r.status_code}: {r.text[:300]}")

# ---------------------------------------------------------------------------
# 5. Verificar estado final
# ---------------------------------------------------------------------------
print("\n=== VERIFICACION FINAL ===")
print("\nPaginas:")
r = requests.get(f'{BASE}/pages?per_page=50', headers=headers)
for p in r.json():
    print(f'  ID={p["id"]} slug={p["slug"]} status={p["status"]} title="{p["title"]["rendered"]}"')

print("\nPosts:")
r = requests.get(f'{BASE}/posts?per_page=50', headers=headers)
posts = r.json()
if not posts:
    print("  (ninguno)")
else:
    for p in posts:
        print(f'  ID={p["id"]} slug={p["slug"]} title="{p["title"]["rendered"]}"')

print("\n=== LISTO ===")
