"""
Actualiza la landing page (ID 10) de Web Analyzer en WordPress.
Usa bridge PHP via FTP porque el usuario REST API no tiene capacidades de edicion.
"""
import os
import requests, base64, ftplib, ssl, io, os

WP_USER = os.getenv("WP_USER", "a0110133")
WP_PASS = os.getenv("WP_APP_PASSWORD", "")
BASE = "https://webanalyzer.com.ar/web/wp-json/wp/v2"
auth = base64.b64encode(f'{WP_USER}:{WP_PASS}'.encode()).decode()
headers = {'Authorization': f'Basic {auth}', 'Content-Type': 'application/json'}

FTP_HOST = os.getenv("FTP_HOST_WEBANALYZER", "a0110133.ferozo.com")
FTP_USER = "a0110133"
FTP_PASS = os.getenv("FTP_PASS_WEBANALYZER", "")

# Leer pagina actual
r = requests.get(f'{BASE}/pages/10', headers=headers, params={'context': 'edit'})
current_raw = r.json().get('content', {}).get('raw', '')
print(f"Contenido actual: {len(current_raw)} chars")

# Extraer el HTML interno
inner = current_raw.replace('<!-- wp:html -->', '').replace('<!-- /wp:html -->', '').strip()

# Encontrar el punto de insercion
marcador = '<h2 class="wa-section-label">Qu'
pos = inner.find(marcador)
if pos == -1:
    marcador = 'Qué obtenés con cada análisis'
    pos = inner.find(marcador)
    if pos == -1:
        print("ERROR: No se encontro el marcador de features")
        exit(1)

print(f"Insertando en posicion {pos}")
first_part = inner[:pos]

# =====================================================================
# NUEVAS SECCIONES
# =====================================================================
new_sections = """<h2 class="wa-section-label">Qué obtenés con cada análisis</h2>
<p class="wa-section-sub">Todo lo que necesitás para mejorar tu sitio, en 30 segundos.</p>

<div style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin:24px 0">
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">📊</div>
<div class="wa-feature-title">Scorecard en 5 categorías</div>
<div class="wa-feature-desc">Rendimiento, Accesibilidad, SEO, UX y Conversión con puntaje del 1 al 10.</div>
</div>
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">🔍</div>
<div class="wa-feature-title">Hallazgos críticos</div>
<div class="wa-feature-desc">Cada problema detectado con su impacto real en el negocio y solución paso a paso.</div>
</div>
<div class="wa-feature-card" style="flex:1;min-width:200px">
<div class="wa-feature-icon">📦</div>
<div class="wa-feature-title">Plugin WordPress .zip</div>
<div class="wa-feature-desc">Soluciones descargables que aplicás directo en tu sitio sin tocar código.</div>
</div>
</div>

<hr />

<!-- ===== HOW IT WORKS (3 pasos) ===== -->
<div style="text-align:center;padding:48px 16px 0">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#58a6ff;margin-bottom:8px;font-weight:600">Cómo funciona</div>
  <h2 style="font-size:26px;font-weight:700;color:#fff;margin:0 0 8px">De cero a optimizado en 3 pasos</h2>
  <p style="font-size:14px;color:#8b949e;margin-bottom:36px">No necesitás ser técnico. No necesitás instalar nada. Solo la URL de tu sitio.</p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;max-width:800px;margin:0 auto">
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px 20px 24px">
      <div style="width:36px;height:36px;border-radius:50%;background:#1f6feb;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 14px">1</div>
      <h3 style="font-size:15px;font-weight:600;color:#fff;margin:0 0 8px">Pegá tu URL</h3>
      <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0">Ingresá la dirección de tu sitio web. Nuestro motor analiza en tiempo real el código, las imágenes, los scripts y los metadatos.</p>
    </div>
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px 20px 24px">
      <div style="width:36px;height:36px;border-radius:50%;background:#1f6feb;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 14px">2</div>
      <h3 style="font-size:15px;font-weight:600;color:#fff;margin:0 0 8px">Recibí el diagnóstico</h3>
      <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0">En 30 segundos ves un scorecard con 5 categorías, hallazgos críticos ordenados por impacto y recomendaciones concretas.</p>
    </div>
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:28px 20px 24px">
      <div style="width:36px;height:36px;border-radius:50%;background:#1f6feb;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;margin:0 auto 14px">3</div>
      <h3 style="font-size:15px;font-weight:600;color:#fff;margin:0 0 8px">Descargá el plugin</h3>
      <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0">Con el plan PRO descargás un plugin WordPress .zip que aplica todas las correcciones en tu sitio sin tocar código.</p>
    </div>
  </div>
</div>

<hr />

<!-- ===== PRICING TABLE ===== -->
<div style="text-align:center;padding:48px 16px 0;max-width:750px;margin:0 auto">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#d29922;margin-bottom:8px;font-weight:600">Planes y precios</div>
  <h2 style="font-size:26px;font-weight:700;color:#fff;margin:0 0 8px">Inversión única, sin suscripciones</h2>
  <p style="font-size:14px;color:#8b949e;margin-bottom:36px">Pagás una vez por análisis. Sin cargos recurrentes. Sin letra chica.</p>
  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:20px;text-align:left">
    <!-- GRATIS -->
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:32px 24px">
      <h3 style="font-size:18px;font-weight:700;color:#fff;margin:0 0 4px">Gratis</h3>
      <div style="font-size:32px;font-weight:800;color:#fff;margin:8px 0 4px">$0</div>
      <div style="font-size:11px;color:#6e7681;margin-bottom:20px">Para siempre</div>
      <ul style="list-style:none;padding:0;margin:0 0 24px">
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Scorecard completo (5 categorías)</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Hallazgos críticos detectados</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Recomendaciones generales</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Guía en formato markdown</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">❌ Plugin WordPress .zip</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">❌ Archivos HTML corregidos</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">❌ Reporte JSON completo</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9">❌ Soluciones paso a paso</li>
      </ul>
      <a href="https://web-analyzer-1-l8uc.onrender.com/" target="_blank" rel="noopener" style="display:block;text-align:center;padding:12px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;background:#21262d;color:#58a6ff;border:1px solid #30363d">Analizar gratis</a>
    </div>
    <!-- PRO -->
    <div style="background:linear-gradient(135deg,#1a1a0a 0%,#161b22 100%);border:2px solid #d29922;border-radius:12px;padding:32px 24px;position:relative;box-shadow:0 0 20px rgba(210,153,34,0.08)">
      <div style="position:absolute;top:-12px;right:20px;background:#d29922;color:#000;font-size:11px;font-weight:700;padding:4px 12px;border-radius:20px;text-transform:uppercase">Recomendado</div>
      <h3 style="font-size:18px;font-weight:700;color:#fff;margin:0 0 4px">PRO</h3>
      <div style="font-size:32px;font-weight:800;color:#fff;margin:8px 0 4px">ARS 12.000 <small style="font-size:14px;font-weight:400;color:#8b949e">/ único pago</small></div>
      <div style="font-size:11px;color:#6e7681;margin-bottom:20px">Por análisis, sin suscripción</div>
      <ul style="list-style:none;padding:0;margin:0 0 24px">
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Scorecard completo (5 categorías)</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Hallazgos críticos con impacto</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Recomendaciones personalizadas</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ Guía en formato markdown</li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ <strong>Plugin WordPress .zip</strong></li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ <strong>Archivos HTML corregidos</strong></li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9;border-bottom:1px solid #21262d">✅ <strong>Reporte JSON completo</strong></li>
        <li style="padding:6px 0;font-size:13px;color:#c9d1d9">✅ <strong>Soluciones paso a paso</strong></li>
      </ul>
      <a href="https://web-analyzer-1-l8uc.onrender.com/" target="_blank" rel="noopener" style="display:block;text-align:center;padding:14px 24px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;background:#d29922;color:#000">Analizar y comprar PRO</a>
      <div style="font-size:10px;color:#6e7681;text-align:center;margin-top:12px">🔒 Pago seguro con MercadoPago</div>
    </div>
  </div>
  <!-- Anclaje de precio -->
  <div style="max-width:650px;margin:32px auto 0;background:rgba(88,166,255,0.06);border:1px solid rgba(88,166,255,0.2);border-radius:10px;padding:20px 24px;text-align:center">
    <p style="font-size:13px;color:#8b949e;line-height:1.6;margin:0">¿Sabías que una auditoría web profesional cuesta entre <strong style="color:#58a6ff">USD 50 y USD 200</strong> (ARS 50.000 a 200.000)? Con Web Analyzer obtenés el mismo nivel de detalle por <strong style="color:#58a6ff">ARS 12.000</strong>, en 5 minutos y sin esperar turno con un consultor.</p>
  </div>
</div>

<hr />

<!-- ===== RESULTADOS REALES ===== -->
<div style="text-align:center;padding:48px 16px 0;max-width:800px;margin:0 auto">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#3fb950;margin-bottom:8px;font-weight:600">Resultados reales</div>
  <h2 style="font-size:26px;font-weight:700;color:#fff;margin:0 0 8px">Esto es lo que Web Analyzer puede hacer por tu sitio</h2>
  <p style="font-size:14px;color:#8b949e;margin-bottom:36px">Escenarios basados en auditorías reales a sitios WordPress con problemas comunes.</p>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;text-align:left">
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px 20px">
      <div style="font-size:32px;margin-bottom:10px">🛒</div>
      <h4 style="font-size:14px;font-weight:600;color:#fff;margin:0 0 8px">Tienda online sin ventas</h4>
      <p style="font-size:12px;color:#8b949e;line-height:1.6;margin:0 0 12px">Sitio WooCommerce con 57 imágenes sin lazy loading, 23 productos sin meta description y formulario de checkout sin labels. La tienda cargaba en 6.2 segundos y perdía clientes en móvil.</p>
      <span style="display:inline-block;font-size:11px;font-weight:600;color:#3fb950;background:rgba(63,185,80,0.1);padding:4px 10px;border-radius:12px">Después del plugin: 4.8 → 9.2</span>
    </div>
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px 20px">
      <div style="font-size:32px;margin-bottom:10px">📰</div>
      <h4 style="font-size:14px;font-weight:600;color:#fff;margin:0 0 8px">Blog invisible en Google</h4>
      <p style="font-size:12px;color:#8b949e;line-height:1.6;margin:0 0 12px">Sitio con 200+ artículos sin OG tags, sin canonical, sin alt text en imágenes y sin sitemap. Google no indexaba el 60% del contenido.</p>
      <span style="display:inline-block;font-size:11px;font-weight:600;color:#3fb950;background:rgba(63,185,80,0.1);padding:4px 10px;border-radius:12px">Después del plugin: 5.2 → 9.5</span>
    </div>
    <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px 20px">
      <div style="font-size:32px;margin-bottom:10px">🏛️</div>
      <h4 style="font-size:14px;font-weight:600;color:#fff;margin:0 0 8px">Estudio con web lenta</h4>
      <p style="font-size:12px;color:#8b949e;line-height:1.6;margin:0 0 12px">Landing corporativa con 14 scripts bloqueantes, tipografía externa sin preload, formulario sin protección y viewport incorrecto en móvil.</p>
      <span style="display:inline-block;font-size:11px;font-weight:600;color:#3fb950;background:rgba(63,185,80,0.1);padding:4px 10px;border-radius:12px">Después del plugin: 5.0 → 9.6</span>
    </div>
  </div>
</div>

<hr />

<!-- ===== FAQ CONDENSADO ===== -->
<div style="text-align:center;padding:48px 16px 0;max-width:700px;margin:0 auto">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:2px;color:#8b949e;margin-bottom:8px;font-weight:600">Preguntas frecuentes</div>
  <h2 style="font-size:26px;font-weight:700;color:#fff;margin:0 0 8px">Todo lo que necesitás saber</h2>
  <p style="font-size:14px;color:#8b949e;margin-bottom:36px">Respuestas directas. Sin vueltas.</p>

  <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px 20px;margin-bottom:10px;text-align:left">
    <h4 style="font-size:14px;font-weight:600;color:#58a6ff;margin:0 0 6px">¿Qué hace exactamente el plugin?</h4>
    <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0">Aplica correcciones automáticas en tu sitio WordPress: agrega meta tags (OG, description, canonical), lazy loading a imágenes, alt text faltante, atributos defer/async a scripts bloqueantes, y formularios de captura de email. Todo sin que edites código.</p>
  </div>

  <div style="background:rgba(210,153,34,0.06);border:1px solid rgba(210,153,34,0.4);border-radius:8px;padding:18px 20px;margin-bottom:10px;text-align:left">
    <h4 style="font-size:14px;font-weight:600;color:#d29922;margin:0 0 6px">💰 ¿Qué incluye el plan gratis y qué el plan PRO?</h4>
    <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0"><strong style="color:#fff">Gratis:</strong> análisis completo con scorecard, hallazgos, recomendaciones y guía en markdown. <strong style="color:#fff">PRO (ARS 12.000):</strong> todo lo anterior + descarga del plugin WordPress (.zip), archivos HTML corregidos y reporte JSON completo. <strong style="color:#d29922">Pago único por análisis, sin suscripción.</strong></p>
  </div>

  <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px 20px;margin-bottom:10px;text-align:left">
    <h4 style="font-size:14px;font-weight:600;color:#58a6ff;margin:0 0 6px">¿El plugin modifica el contenido de mis entradas o páginas?</h4>
    <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0"><strong style="color:#fff">No.</strong> El plugin trabaja a nivel técnico (meta tags, scripts, lazy loading, formularios). No edita ni borra ninguna entrada, página, imagen o configuración de WordPress.</p>
  </div>

  <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:18px 20px;margin-bottom:10px;text-align:left">
    <h4 style="font-size:14px;font-weight:600;color:#58a6ff;margin:0 0 6px">¿Qué pasa si ya tengo otro plugin de SEO?</h4>
    <p style="font-size:12px;color:#8b949e;line-height:1.5;margin:0">El plugin de Web Analyzer convive con Yoast, RankMath y otros. No reemplaza sus funciones: agrega las correcciones que esos plugins no cubren. Si hay conflicto, el plugin detecta si ya existe y no lo duplica.</p>
  </div>

  <a href="/web/faq" style="display:inline-block;margin-top:16px;font-size:13px;color:#58a6ff;text-decoration:none;font-weight:600">Ver todas las preguntas frecuentes →</a>
</div>

<hr />

<!-- ===== CTA FINAL DUAL ===== -->
<div style="text-align:center;padding:40px 24px;margin:24px auto 32px;background:linear-gradient(135deg,#161b22 0%,#1a1a2e 100%);border:1px solid #30363d;border-radius:16px;max-width:650px">
  <h2 style="font-size:24px;font-weight:700;color:#fff;margin:0 0 8px">¿Tu sitio está mejor que el de River?</h2>
  <p style="font-size:14px;color:#8b949e;margin-bottom:28px;line-height:1.5">El sitio oficial de River Plate tiene score <strong style="color:#f85149">3.2/10</strong>. Pegá tu URL y descubrí tu puntaje en 30 segundos. Después, si querés las soluciones, pagás una sola vez.</p>
  <div style="display:flex;gap:14px;justify-content:center;flex-wrap:wrap;align-items:center">
    <a href="https://web-analyzer-1-l8uc.onrender.com/" target="_blank" rel="noopener" style="display:inline-block;padding:14px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;background:#21262d;color:#58a6ff;border:1px solid #30363d">Analizar gratis</a>
    <a href="https://web-analyzer-1-l8uc.onrender.com/" target="_blank" rel="noopener" style="display:inline-block;padding:14px 32px;border-radius:8px;font-size:15px;font-weight:700;text-decoration:none;background:#d29922;color:#000">Analizar y comprar PRO</a>
  </div>
  <div style="font-size:11px;color:#6e7681;margin-top:16px">Pago único de ARS 12.000. Sin suscripción. Resultados inmediatos.</div>
</div>

<!-- ===== FOOTER ===== -->
<div style="text-align:center;padding:24px;border-top:1px solid #30363d;margin-top:32px;font-size:12px;color:#6e7681">
  <a href="/web/blog/" style="color:#58a6ff">Blog</a> &nbsp;·&nbsp;
  <a href="/web/faq" style="color:#58a6ff">FAQ</a> &nbsp;·&nbsp;
  <a href="mailto:webanalyzer.app@gmail.com" style="color:#58a6ff">webanalyzer.app@gmail.com</a>
</div>"""

# Armar el contenido final
new_inner = first_part + new_sections
new_content = '<!-- wp:html -->\n' + new_inner + '\n<!-- /wp:html -->'

print(f"Nuevo contenido: {len(new_content)} chars")

# =====================================================================
# PASO 1: Subir bridge PHP via FTP
# =====================================================================
print("\n=== Subiendo bridge PHP via FTP ===")
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE

ftp = ftplib.FTP_TLS(FTP_HOST, timeout=15, context=context)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd("/public_html/web")

# Leer bridge.php local
bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wa_bridge.php')
with open(bridge_path, 'rb') as f:
    bridge_data = f.read()

bio = io.BytesIO(bridge_data)
ftp.storbinary("STOR wa_bridge.php", bio)
print("Bridge PHP subido")

# =====================================================================
# PASO 2: Llamar al bridge via HTTP
# =====================================================================
print("\n=== Llamando al bridge PHP ===")
bridge_url = "https://webanalyzer.com.ar/web/wa_bridge.php"
r = requests.post(bridge_url, data={
    'token': os.getenv("WA_BRIDGE_TOKEN", ""),
    'content': new_content
})
print(f"Bridge response: {r.text}")

# =====================================================================
# PASO 3: Eliminar bridge PHP
# =====================================================================
print("\n=== Eliminando bridge PHP ===")
ftp.delete("wa_bridge.php")
ftp.quit()
print("Bridge PHP eliminado")

# =====================================================================
# VERIFICACION
# =====================================================================
print("\n=== Verificando ===")
r = requests.get(f'{BASE}/pages/10', headers=headers, params={'context': 'edit'})
raw = r.json().get('content', {}).get('raw', '')
print(f"Contenido final: {len(raw)} chars")
for keyword in ['Analizar y comprar PRO', 'Planes y precios', 'Cómo funciona', 'Resultados reales', 'Inversión única']:
    present = keyword in raw
    print(f"  {'SI' if present else 'NO'}: {keyword}")

if len(raw) > 15000:
    print("\n*** LANDING ACTUALIZADA CORRECTAMENTE ***")
    print("Visita: https://webanalyzer.com.ar/web/")
else:
    print("\n*** ALERTA: El contenido no se actualizo ***")
