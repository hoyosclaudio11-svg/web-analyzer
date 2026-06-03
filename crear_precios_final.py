"""Crear pagina de Precios con contenido completo usando HTTPS."""
import os
import requests, base64, json

BASE = 'https://webanalyzer.com.ar/web/wp-json/wp/v2'
_wp_user = os.getenv("WP_USER", "a0110133")
_wp_pass = os.getenv("WP_APP_PASSWORD", "")
auth = base64.b64encode(f"{_wp_user}:{_wp_pass}".encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

# Borrar la pagina de prueba (ID=64) si existe
print("Eliminando pagina de prueba...")
r = requests.delete(f'{BASE}/pages/64?force=true', headers=headers)
print(f"  Status: {r.status_code}")

# Crear pagina de precios con contenido completo
PRICING_HTML = """<h2 style="text-align:center;font-size:2rem;margin-bottom:8px">Planes simples, sin vueltas</h2>
<p style="text-align:center;color:#aaa;font-size:1.05rem;margin-bottom:48px">Un solo pago. Sin suscripciones. Sin letra chica.</p>

<div style="display:flex;gap:24px;justify-content:center;flex-wrap:wrap;max-width:900px;margin:0 auto">

<div style="flex:1;min-width:280px;max-width:400px;background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px 24px;text-align:center">
  <h3 style="color:#fff;font-size:1.3rem;margin:0 0 8px">Gratis</h3>
  <p style="color:#8b949e;font-size:0.9rem;margin:0 0 20px">Diagnostico instantaneo</p>
  <div style="font-size:2.5rem;font-weight:700;color:#58a6ff;margin-bottom:20px">$0</div>
  <ul style="list-style:none;padding:0;text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:2">
    <li>Scorecard 0-10 en 5 categorias</li>
    <li>Hallazgos criticos detectados</li>
    <li>Tecnologia del sitio identificada</li>
    <li>Link publico compartible</li>
    <li style="color:#6e7681">Soluciones descargables</li>
    <li style="color:#6e7681">Plugin WordPress .zip</li>
    <li style="color:#6e7681">Reporte JSON completo</li>
  </ul>
  <a href="https://web-analyzer-1-l8uc.onrender.com/" style="display:block;margin-top:24px;padding:12px;background:#30363d;color:#c9d1d9;border-radius:8px;text-decoration:none;font-weight:600">Analizar gratis</a>
</div>

<div style="flex:1;min-width:280px;max-width:400px;background:#161b22;border:2px solid #1f6feb;border-radius:12px;padding:32px 24px;text-align:center;position:relative">
  <div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%);background:#1f6feb;color:#fff;padding:4px 16px;border-radius:20px;font-size:0.8rem;font-weight:600">RECOMENDADO</div>
  <h3 style="color:#fff;font-size:1.3rem;margin:0 0 8px">Analisis completo</h3>
  <p style="color:#8b949e;font-size:0.9rem;margin:0 0 20px">Diagnostico + soluciones</p>
  <div style="font-size:2.5rem;font-weight:700;color:#fff;margin-bottom:4px">ARS 12.000</div>
  <div style="color:#8b949e;font-size:0.8rem;margin-bottom:20px">Pago unico. No se renueva.</div>
  <ul style="list-style:none;padding:0;text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:2">
    <li>Todo lo del plan Gratis</li>
    <li>Plugin WordPress .zip listo para instalar</li>
    <li>Correcciones automaticas (SEO, lazy loading, OG tags, CTAs)</li>
    <li>Reporte JSON descargable</li>
    <li>Soluciones paso a paso por categoria</li>
    <li>Acceso al historial de analisis</li>
    <li>Soporte por email</li>
  </ul>
  <a href="https://web-analyzer-1-l8uc.onrender.com/" style="display:block;margin-top:24px;padding:12px;background:#1f6feb;color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.05rem">Analizar y comprar</a>
</div>

</div>

<div style="max-width:700px;margin:48px auto 0;text-align:center;color:#8b949e;font-size:0.9rem;line-height:1.8">

<h3 style="color:#fff;font-size:1.2rem;margin-bottom:16px">Por que un pago unico?</h3>

<p>Una auditoria profesional con una agencia cuesta entre <strong style="color:#fff">$50.000 y $200.000 ARS</strong>. Web Analyzer te da el mismo nivel de detalle por <strong style="color:#58a6ff">$12.000 ARS</strong>, en 30 segundos, sin esperar turno.</p>

<p style="margin-top:20px"><strong style="color:#fff">Sin suscripcion. Sin cuotas escondidas.</strong> Pagas una vez, descargas tu plugin, y es tuyo para siempre.</p>

</div>

<div style="max-width:700px;margin:40px auto 0;padding:24px;background:rgba(31,111,235,0.08);border:1px solid rgba(31,111,235,0.25);border-radius:12px;text-align:center">

<h3 style="color:#fff;font-size:1.1rem;margin:0 0 12px">Garantia de 7 dias</h3>

<p style="color:#8b949e;font-size:0.9rem;margin:0">Si despues de aplicar las soluciones tu sitio no mejora al menos <strong style="color:#fff">una categoria</strong> del scorecard, te devolvemos el 100% del dinero. Sin preguntas.</p>

</div>

<div style="max-width:700px;margin:40px auto 0;text-align:center">

<h3 style="color:#fff;font-size:1.2rem;margin-bottom:16px">Preguntas frecuentes</h3>

<div style="text-align:left;color:#c9d1d9;font-size:0.9rem;line-height:1.7">

<p><strong style="color:#fff">Necesito saber de programacion?</strong><br>No. El plugin se instala como cualquier plugin de WordPress. Un clic, activar, y las correcciones se aplican solas.</p>

<p><strong style="color:#fff">Funciona en sitios que no son WordPress?</strong><br>El analisis funciona en cualquier URL publica. Las soluciones descargables incluyen un archivo HTML con correcciones manuales y un JSON con todos los datos para que tu desarrollador los implemente.</p>

<p><strong style="color:#fff">Cuantos analisis incluye el pago?</strong><br>Un analisis completo por URL. Si necesitas analizar varios sitios, cada uno requiere su compra individual.</p>

<p><strong style="color:#fff">Que formas de pago aceptan?</strong><br>MercadoPago: tarjeta de credito, debito, transferencia, y efectivo en puntos de pago.</p>

<p><strong style="color:#fff">Cuanto tarda el analisis?</strong><br>Menos de 30 segundos. Procesamos tu URL en tiempo real y ves los resultados instantaneamente.</p>

</div>

</div>"""

payload = {
    'title': 'Precios',
    'slug': 'precios',
    'content': PRICING_HTML,
    'status': 'publish',
}

print("\nCreando pagina de Precios...")
r = requests.post(f'{BASE}/pages', headers=headers, json=payload)
if r.status_code == 201:
    data = r.json()
    print(f"  CREADA - ID={data['id']}")
    print(f"  URL: {data['link']}")
else:
    print(f"  ERROR {r.status_code}: {r.text[:300]}")
    # Si ya existe, actualizar
    print("\nBuscando pagina existente...")
    r = requests.get(f'{BASE}/pages?slug=precios', headers=headers)
    pages = r.json()
    if pages:
        pid = pages[0]['id']
        print(f"  Encontrada ID={pid}. Actualizando...")
        r = requests.post(f'{BASE}/pages/{pid}', headers=headers, json=payload)
        if r.status_code in (200, 201):
            print(f"  ACTUALIZADA - ID={pid}")
        else:
            print(f"  ERROR {r.status_code}: {r.text[:300]}")

# Verificar
print("\n=== PAGINAS FINALES ===")
r = requests.get(f'{BASE}/pages?per_page=20', headers=headers)
for p in r.json():
    print(f"  ID={p['id']} slug={p['slug']} status={p['status']} title=\"{p['title']['rendered']}\"")

print("\n=== LISTO ===")
print("Landing: https://webanalyzer.com.ar/web/")
print("Precios: https://webanalyzer.com.ar/web/precios/")
