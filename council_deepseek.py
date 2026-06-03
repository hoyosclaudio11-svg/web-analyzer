"""
CONSEJO RIVER PLATE INFO — 7 personalidades vía DeepSeek API
Cada miembro audita el sitio desde su perspectiva.
"""
import os, requests, json

API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not API_KEY:
    raise RuntimeError("DEEPSEEK_API_KEY no configurada")
API_URL = "https://api.deepseek.com/v1/chat/completions"
SITE_URL = "https://riverplate-info.com.ar"

# Las 7 personalidades del consejo
COUNCIL = [
    {
        "name": "Diseñador UX Senior",
        "role": "system",
        "prompt": """Sos un diseñador UX senior con 15 años de experiencia. Tu especialidad es usabilidad, legibilidad y experiencia de usuario en sitios web. Al evaluar un sitio mirás: jerarquía visual, espacios en blanco, legibilidad de textos, navegación intuitiva, responsividad, y si el diseño guía al usuario naturalmente. Sos crítico pero constructivo. Respondé en español argentino, breve y directo (máximo 5 observaciones)."""
    },
    {
        "name": "Hincha de River",
        "role": "system",
        "prompt": """Sos un hincha fanático de River Plate, socio del club hace 20 años. Vas al Monumental todos los partidos. Evaluás el sitio como hincha: ¿transmite la pasión riverplatense? ¿Los colores y la identidad visual te hacen sentir representado? ¿La información deportiva (plantilla, partidos, tabla) es correcta y completa? ¿Te emociona visitar este sitio? Respondé en español argentino, con pasión, breve y directo (máximo 5 observaciones)."""
    },
    {
        "name": "Abogado Especialista",
        "role": "system",
        "prompt": """Sos un abogado especialista en propiedad intelectual, marcas registradas y derecho deportivo en Argentina. Evaluás el sitio desde la perspectiva legal: ¿hay riesgo de confusión con el sitio oficial del club? ¿Los disclaimers son suficientes? ¿El uso de la marca "River Plate" es adecuado para un sitio de noticias? ¿Hay infracciones a derechos de imagen? ¿El sitio deja claro que NO es oficial? Respondé en español argentino, preciso y breve (máximo 5 observaciones)."""
    },
    {
        "name": "Periodista Deportivo",
        "role": "system",
        "prompt": """Sos un periodista deportivo argentino con 20 años cubriendo fútbol de primera división. Evaluás el sitio como medio de comunicación: ¿la información está actualizada? ¿Las noticias son relevantes? ¿La cobertura del equipo es completa (partidos, plantilla, tabla)? ¿El sitio funciona como fuente de información confiable para un hincha? ¿Qué le falta para ser un medio digital competitivo? Respondé en español argentino, breve y directo (máximo 5 observaciones)."""
    },
    {
        "name": "SEO Specialist",
        "role": "system",
        "prompt": """Sos un especialista en SEO y marketing digital para sitios de noticias deportivas en Argentina. Evaluás el sitio desde posicionamiento: ¿títulos optimizados? ¿Estructura de URLs? ¿Velocidad de carga? ¿Meta descriptions? ¿Contenido indexable? ¿Intención de búsqueda cubierta? ¿El sitio puede rankear para "noticias River Plate"? Respondé en español argentino, breve y directo (máximo 5 observaciones)."""
    },
    {
        "name": "Web Developer",
        "role": "system",
        "prompt": """Sos un desarrollador web full-stack especializado en WordPress y sitios de alto tráfico. Evaluás el aspecto técnico: ¿CSS bien estructurado? ¿Buen uso de Bootstrap? ¿Problemas de compatibilidad? ¿Errores visibles en consola? ¿Shortcodes funcionando correctamente? ¿La integración con SportsPress es correcta? ¿Problemas de layout o CSS quebrado? Respondé en español argentino, breve y directo (máximo 5 observaciones)."""
    },
    {
        "name": "Editor General",
        "role": "system",
        "prompt": """Sos el editor general de un diario deportivo digital. Tu trabajo es dar el veredicto final sobre si un sitio está listo para publicarse. Integrás las perspectivas de diseño, contenido, legales y técnico. Das un veredicto: APROBADO (listo para publicar), APROBADO CON OBSERVACIONES (funciona pero necesita ajustes), o RECHAZADO (necesita cambios mayores). Respondé en español argentino, breve (máximo 3 párrafos)."""
    },
]

def query_deepseek(system_prompt, user_message):
    """Llama a la API DeepSeek con un system prompt específico."""
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
        "max_tokens": 600,
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            data = r.json()
            return data["choices"][0]["message"]["content"]
        return f"ERROR API: {r.status_code} - {r.text[:200]}"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    # Fetch las páginas para auditar
    print("=" * 80)
    print("  CONSEJO RIVER PLATE INFO — 7 Personalidades vía DeepSeek Pro v4")
    print("=" * 80)

    # User message con las URLs a revisar
    pages = [
        f"{SITE_URL}/ (Inicio)",
        f"{SITE_URL}/plantilla (Plantilla)",
        f"{SITE_URL}/calendario (Calendario)",
        f"{SITE_URL}/noticias (Noticias)",
        f"{SITE_URL}/tienda (Tienda)",
    ]

    user_msg = f"""Auditá el sitio {SITE_URL}, un portal de noticias e información NO OFICIAL sobre el Club Atlético River Plate. Revisá específicamente estas páginas:
{chr(10).join(pages)}

El sitio usa WordPress + tema Newsup + plugin SportsPress. Paleta de colores: negro (#111), rojo (#e63946), blanco. Tiene 25 jugadores en plantilla, 19 partidos (14 jugados + 5 próximos), 21 equipos en tabla de posiciones, y una sección de productos de MercadoLibre vía afiliados.

Dame tu evaluación profesional sincera."""

    results = {}
    for i, member in enumerate(COUNCIL):
        name = member["name"]
        print(f"\n--- Consejero {i+1}/7: {name} ---")
        print("Consultando a DeepSeek...", end=" ", flush=True)
        response = query_deepseek(member["prompt"], user_msg)
        results[name] = response
        print("OK")
        print(response[:600])
        if len(response) > 600:
            print("...")

    print("\n" + "=" * 80)
    print("  VEREDICTOS COMPLETOS")
    print("=" * 80)
    for name, text in results.items():
        print(f"\n### {name} ###")
        print(text)

    # Save to file
    with open("E:/DelMonte/web-analyzer/council_verdict.md", "w", encoding="utf-8") as f:
        f.write("# Consejo River Plate Info — Auditoría IA\n\n")
        f.write(f"Sitio: {SITE_URL}\n")
        f.write(f"Fecha: 2026-05-15\n")
        f.write(f"Modelo: DeepSeek Pro v4 (deepseek-chat)\n\n")
        f.write("---\n\n")
        for name, text in results.items():
            f.write(f"## {name}\n\n{text}\n\n---\n\n")
    print("\nVeredictos guardados en council_verdict.md")

if __name__ == "__main__":
    main()
