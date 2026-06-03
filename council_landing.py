"""
CONSEJO DE VENTAS v2 — Audita webanalyzer.com.ar/web/ (WordPress)
La landing page OFICIAL que vende el Web Analyzer.
"""
import requests, json, os
from datetime import datetime

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY no configurada")
API_URL = "https://api.deepseek.com/v1/chat/completions"

COUNCIL = [
    {
        "name": "Especialista en UX y Conversión",
        "role": "system",
        "prompt": """Sos un especialista en UX y optimización de conversión con 12 años en SaaS. Evaluás páginas de venta: jerarquía visual, claridad del mensaje, fricción en el funnel, CTAs, pruebas sociales, manejo de objeciones, y si el usuario entiende en 5 segundos qué hace el producto. Sos crítico, directo. Respondé en español argentino, máximo 6 observaciones. Cada una: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en Copywriting de Ventas",
        "role": "system",
        "prompt": """Sos un copywriter senior especializado en páginas de venta SaaS en Latinoamérica. Evaluás: headlines, propuesta de valor única, lenguaje beneficios vs características, manejo de objeciones (precio, confianza), CTAs persuasivos, y si el copy habla el idioma del cliente ideal. Respondé en español argentino, máximo 6 observaciones con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Growth Marketer LatAm",
        "role": "system",
        "prompt": """Sos un growth marketer especializado en lanzamientos de SaaS en Argentina. Evaluás: estrategia de adquisición, retención, embudos de conversión, métricas, growth loops. ¿Está preparado para escalar? ¿Tiene mecanismos de retención? ¿El modelo es sostenible? Respondé en español argentino, máximo 5 observaciones con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en Pricing y Monetización",
        "role": "system",
        "prompt": """Sos un consultor de pricing para SaaS en Argentina. Evaluás: ¿ARS 12.000 es el precio correcto? ¿Pago único vs suscripción? ¿Valor percibido? ¿El usuario entiende qué gana al pagar? ¿Debería haber planes escalonados? Respondé en español argentino, máximo 5 observaciones con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en SEO y Contenido",
        "role": "system",
        "prompt": """Sos un especialista en SEO y marketing de contenidos. Evaluás esta landing WordPress: ¿está optimizada para rankear? ¿El blog tiene sentido o está abandonado? ¿Hay contenido que atraiga tráfico orgánico? ¿La estructura de URLs es correcta? ¿Falta contenido clave? Respondé en español argentino, máximo 5 observaciones con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "WordPress Developer Senior",
        "role": "system",
        "prompt": """Sos un desarrollador WordPress senior. Evaluás: ¿el tema es adecuado para una landing de ventas? ¿Los plugins son correctos? ¿La estructura de la página es mantenible? ¿Hay problemas de performance o seguridad evidentes? ¿Falta algo técnico crítico (SSL, formularios, analytics)? Respondé en español argentino, máximo 5 observaciones con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Director de Producto SaaS",
        "role": "system",
        "prompt": """Sos un director de producto con 15 años lanzando SaaS. Das un veredicto final integrando diseño, copy, pricing, growth, SEO y aspectos técnicos. Respondés: ¿está listo para vender? ¿Cuáles son los 3 cambios más urgentes? ¿Cuál es la propuesta de valor real que debería comunicar? Veredicto final. Respondé en español argentino, 3-4 párrafos concretos y accionables."""
    },
]

SITE_AUDIT = """Auditá la landing page de ventas del Web Analyzer.

URL: https://webanalyzer.com.ar/web/

PRODUCTO: Herramienta SaaS que analiza cualquier URL pública y genera una auditoría en 5 categorías (Rendimiento, Accesibilidad, SEO, UX, Conversión) con puntaje 0-10, hallazgos, recomendaciones y soluciones descargables (plugin WordPress .zip, JSON). PRECIO: ARS 12.000 pago único por análisis. El análisis básico (scorecard + hallazgos) es GRATIS. Las descargas son pagas. La herramienta real está en Render (web-analyzer-1-l8uc.onrender.com), pero la landing de ventas está en este WordPress.

LO QUE TIENE LA LANDING ACTUAL:
- Hero section con propuesta de valor y CTA "Analizar mi sitio gratis" que va a Render
- Carrusel de auditorías de ejemplo (River Plate 3.2/10, Yahoo 4.8/10, Boca Juniors 6.0/10, Olé 6.6/10) con link "Analizar ahora" para cada uno
- Antes/después de 3 sitios WordPress que mejoraron de ~5.5 a 9.6 con capturas de pantalla
- Features destacadas: scorecard 0-10, hallazgos con impacto en negocio, plugin WordPress descargable
- Footer con link al blog y email de contacto
- Tema: parece ser Twenty Twenty-Three o similar (WordPress básico)
- Solo 2 páginas en el sitio: Home (landing) y Blog
- El blog se llama "Mente despierta: un blog sobre filosofía" y tiene solo 5 posts, incluyendo un "Hola mundo" de 2013 y posts duplicados
- Sin página de precios, sin FAQ, sin features dedicada, sin testimonios reales, sin política de privacidad, sin términos
- Sin formulario de contacto, sin chat, sin newsletter
- Sin analytics visibles, sin remarketing
- El blog está totalmente abandonado y el tagline "filosofía" no tiene nada que ver con el producto
- Sin metadatos de producto (schema.org), sin OG tags optimizados para ventas

LO QUE NO TIENE (AUSENCIAS CRÍTICAS):
- Página de precios dedicada que explique el valor de ARS 12.000
- Testimonios reales de clientes
- Página "Sobre nosotros" o "Quiénes somos"
- FAQ
- Política de privacidad / Términos y condiciones
- Formulario de captura de leads (email)
- Chat en vivo o WhatsApp Business
- Sección de garantía
- Comparación con competidores o alternativas (consultoría tradicional)
- Proceso claro de 3 pasos (analizás gratis → ves resultados → comprás soluciones)
- Email nurturing post-visita
- Redes sociales

LO BUENO (lo que SÍ funciona):
- Los ejemplos de sitios conocidos (River, Boca, Olé) generan identificación inmediata con el público argentino
- Los casos de antes/después con scores y capturas son buen proof-of-concept
- El CTA "Analizar mi sitio gratis" es claro y la herramienta en Render funciona
- El dominio .com.ar es profesional y local
- El análisis gratuito baja la barrera de entrada
- Las capturas de pantalla reales en los casos de éxito dan credibilidad

Dame tu evaluación profesional sincera y accionable."""

def query_deepseek(system_prompt, user_message):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.8,
        "max_tokens": 900,
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"ERROR API: {r.status_code} - {r.text[:200]}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    print("=" * 80)
    print("  CONSEJO DE VENTAS v2 — webanalyzer.com.ar/web/")
    print("  Auditoría landing page WordPress oficial")
    print("  7 Expertos vía DeepSeek")
    print("=" * 80)

    results = {}
    for i, member in enumerate(COUNCIL):
        name = member["name"]
        print(f"\n--- Consejero {i+1}/7: {name} ---")
        print("Consultando a DeepSeek...", end=" ", flush=True)
        response = query_deepseek(member["prompt"], SITE_AUDIT)
        results[name] = response
        print("OK")
        preview = response[:200]
        try:
            print(preview)
        except UnicodeEncodeError:
            print(preview.encode('ascii', errors='replace').decode())
        if len(response) > 200:
            print("...")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "council_landing_verdict.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Consejo de Ventas — webanalyzer.com.ar/web/ (Landing Oficial)\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("Modelo: DeepSeek (deepseek-chat)\n\n")
        f.write("---\n\n")
        for name, text in results.items():
            f.write(f"## {name}\n\n{text}\n\n---\n\n")

    print(f"\nVeredictos guardados en: {out_path}")

if __name__ == "__main__":
    main()
