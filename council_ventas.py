"""
CONSEJO DE VENTAS — 7 personalidades vía DeepSeek API
Audita el Web Analyzer como página de ventas SaaS.
"""
import requests, json, os
from datetime import datetime

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY no configurada")
API_URL = "https://api.deepseek.com/v1/chat/completions"

# Las páginas del producto a auditar
PAGES = {
    "Landing / Home": "Página principal con el analizador. Hero: '¿Tu web pierde clientes y no sabés por qué?'. Input de URL + botón 'Analizar gratis'. Resultados inline con scorecard 0-10 en 5 categorías (Rendimiento, Accesibilidad, SEO, UX, Conversión). Banner de upgrade: ARS 12.000 para descargar soluciones (plugin WordPress .zip, JSON). CTA post-análisis: 'Crear cuenta gratis' o 'Comprar por ARS 12.000'. Auth modal: login/registro con email y contraseña. Sin onboarding, sin tour, sin testimonios, sin garantía visible.",
    "Features": "Grid 4x2: Rendimiento, Accesibilidad, SEO, UX, Conversión, Plugin WordPress, Scorecard, Re-análisis. Cada card explica qué detecta y qué corrige. CTA final: 'Analizá tu sitio ahora' que redirige al home.",
    "Activación PRO": "Página simple con botón 'Activar PRO'. Usa force-upgrade vía API. Solo para testing. Sin flujo de pago real en esta página.",
    "Checkout Success": "Página post-pago de MercadoPago. Redirige al home con parámetros. Sin mensaje de bienvenida ni onboarding post-compra.",
    "FAQ": "Página de preguntas frecuentes (no se vio el contenido, pero existe el endpoint /faq).",
}

COUNCIL = [
    {
        "name": "Especialista en UX y Conversión",
        "role": "system",
        "prompt": """Sos un especialista en UX y optimización de conversión (CRO) con 12 años de experiencia en SaaS B2B y B2C. Analizás páginas de venta evaluando: jerarquía visual, claridad del mensaje principal, fricción en el funnel, ubicación y diseño de CTAs, pruebas sociales, manejo de objeciones, y si el usuario entiende en 5 segundos qué hace el producto y por qué debería comprarlo. Sos crítico, directo y constructivo. Respondé en español argentino, breve (máximo 6 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en Copywriting de Ventas",
        "role": "system",
        "prompt": """Sos un copywriter senior especializado en páginas de venta SaaS y productos digitales en Latinoamérica. Escribiste copys para más de 200 productos digitales. Evaluás: headlines (¿enganchan?), subheadlines, propuesta de valor única, lenguaje de beneficios vs. características, manejo de objeciones (precio, confianza, competencia), urgencia/escasez, calls-to-action persuasivos, y si el copy habla el idioma del cliente ideal. Respondé en español argentino, breve (máximo 6 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Growth Marketer LatAm",
        "role": "system",
        "prompt": """Sos un growth marketer especializado en lanzamientos de productos digitales en Argentina y Latinoamérica. Tu expertise: estrategias de adquisición, retención, métricas clave, embudos de conversión, marketing de contenidos, y growth loops. Evaluás este SaaS desde la perspectiva de escalabilidad: ¿está preparado para crecer? ¿Tiene mecanismos de retención? ¿El modelo de negocio es sostenible? Respondé en español argentino, breve (máximo 5 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en Pricing y Monetización",
        "role": "system",
        "prompt": """Sos un consultor de pricing y monetización para SaaS. Trabajaste con startups argentinas definiendo modelos de negocio. Evaluás: ¿ARS 12.000 es el precio correcto? ¿Pago único vs. suscripción? ¿El valor percibido justifica el precio? ¿Hay alternativas de pricing (freemium, planes escalonados)? ¿El ancla de valor es clara? ¿El usuario entiende qué gana al pagar? Respondé en español argentino, breve (máximo 5 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Especialista en Checkout y Métodos de Pago",
        "role": "system",
        "prompt": """Sos un especialista en optimización de checkouts y pasarelas de pago para ecommerce en Argentina. Trabajás con MercadoPago, Stripe, y otras pasarelas. Evaluás: fricción en el flujo de pago, cantidad de pasos, claridad del pricing, señales de confianza durante el checkout, post-compra (onboarding, emails, confirmación), y si la integración con MercadoPago Checkout Pro es sólida. Respondé en español argentino, breve (máximo 5 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Desarrollador Full-Stack Senior",
        "role": "system",
        "prompt": """Sos un desarrollador full-stack senior que audita el aspecto técnico de una página de ventas SaaS hecha con Flask + vanilla JS + CSS custom. Evaluás: errores visibles en frontend, performance, estructura HTML semántica, accesibilidad del código, seguridad básica (HTTPS, formularios, CSRF), y si la arquitectura soporta crecimiento. NO evaluás diseño visual — solo aspectos de código y performance. Respondé en español argentino, breve (máximo 5 observaciones), cada una con: Problema → Impacto → Solución concreta."""
    },
    {
        "name": "Director de Producto SaaS",
        "role": "system",
        "prompt": """Sos un director de producto con 15 años lanzando SaaS. Tu trabajo es dar un veredicto final integrando diseño, copy, pricing, growth, checkout y aspectos técnicos. Evaluás: ¿este producto está listo para vender? ¿Cuáles son los 3 cambios de mayor impacto urgente? ¿Cuál es la propuesta de valor REAL que debería comunicar? Das un veredicto final en 3-4 párrafos. Respondé en español argentino, concreto y accionable."""
    },
]

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
    print("  CONSEJO DE VENTAS — Web Analyzer & Optimizer")
    print("  7 Expertos vía DeepSeek")
    print("=" * 80)

    user_msg = """Auditá el Web Analyzer & Optimizer como PÁGINA DE VENTAS SaaS.

PRODUCTO: Herramienta que analiza cualquier URL pública y genera una auditoría en 5 categorías (Rendimiento, Accesibilidad, SEO, UX, Conversión) con puntaje 0-10, hallazgos, recomendaciones y soluciones descargables (plugin WordPress .zip, JSON).

PRECIO: ARS 12.000 pago único por análisis (no suscripción). El análisis básico (scorecard + hallazgos) es GRATIS y sin registro. Las descargas son pagas.

PASARELA DE PAGO: MercadoPago Checkout Pro (Argentina).

PÁGINAS A AUDITAR:
- Home/Landing: Hero '¿Tu web pierde clientes y no sabés por qué?' + input URL + botón 'Analizar gratis'. Resultados inline con scorecard en 5 categorías. Banner upgrade ARS 12.000. CTA post-análisis crea cuenta gratis O compra por ARS 12.000. Auth con email/contraseña. Sin testimonios, sin logos de clientes, sin garantía, sin demo en video, sin tour del producto, sin chat de soporte, sin página de precios dedicada.
- /features: Grid 4x2 con features técnicas. Sin casos de uso, sin ejemplos reales.
- /faq: Preguntas frecuentes.
- Checkout: MercadoPago Checkout Pro externo. Post-compra redirige al home sin onboarding ni email de bienvenida automatizado.
- /activar-pro: Botón de activación manual (solo testing).

LO BUENO DEL PRODUCTO (lo que sí tiene):
- El análisis es instantáneo y gratuito — baja la barrera de entrada
- El scorecard con colores verde/amarillo/rojo es fácil de entender
- Genera soluciones concretas (plugin .zip) no solo diagnóstico
- Tiene link de reporte público compartible (/r/hash)
- Sin suscripción — pago único elimina fricción psicológica

LO QUE PREOCUPA:
- Visitante llega, analiza gratis, ve resultados... ¿y después qué lo motiva a pagar ARS 12.000?
- Sin onboarding ni email post-compra
- Sin pruebas sociales (testimonios, casos de éxito)
- Sin página de pricing dedicada que explique el valor
- El flujo de compra requiere registro previo (fricción extra)
- Sin emails transaccionales ni secuencia de nurturing

Tu tarea es dar observaciones ACCIONABLES que conviertan esto en una página de ventas exitosa para el mercado argentino."""

    results = {}
    for i, member in enumerate(COUNCIL):
        name = member["name"]
        print(f"\n--- Consejero {i+1}/7: {name} ---")
        print("Consultando a DeepSeek...", end=" ", flush=True)
        response = query_deepseek(member["prompt"], user_msg)
        results[name] = response
        print("OK")
        preview = response[:500]
        print(preview)
        if len(response) > 500:
            print("...")

    # Guardar veredictos
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "council_ventas_verdict.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Consejo de Ventas — Web Analyzer & Optimizer\n\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("Modelo: DeepSeek (deepseek-chat)\n\n")
        f.write("---\n\n")
        for name, text in results.items():
            f.write(f"## {name}\n\n{text}\n\n---\n\n")

    print(f"\nVeredictos guardados en: {out_path}")

if __name__ == "__main__":
    main()
