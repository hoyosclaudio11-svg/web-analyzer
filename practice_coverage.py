"""Evidence map for the twenty performance practices in the WebAnalyzer report."""

from __future__ import annotations


def _header(headers, name: str) -> str:
    if not callable(getattr(headers, "get", None)):
        return ""
    value = headers.get(name, "")
    return str(value or "").strip()


def build_practice_coverage(imagenes: dict, scripts: dict, psi: dict | None,
                            response_headers) -> list[dict]:
    audits = {
        audit.get("id"): audit
        for audit in (psi or {}).get("auditorias", [])
        if isinstance(audit, dict) and audit.get("id")
    }

    def lighthouse_state(*ids):
        found = [audits[item] for item in ids if item in audits]
        if not found:
            return "sin_evidencia"
        return "medido" if all(item.get("estado") == "pass" for item in found) else "medido_con_hallazgos"

    encoding = _header(response_headers, "Content-Encoding").lower()
    cache = _header(response_headers, "Cache-Control")
    cdn_headers = (
        "CF-Ray", "CF-Cache-Status", "X-Cache", "X-Cache-Hits", "X-CDN",
        "X-Amz-Cf-Id", "X-Azure-Ref", "Via",
    )
    cdn_signals = [name for name in cdn_headers if _header(response_headers, name)]
    blocking = int((scripts or {}).get("bloqueantes", 0) or 0)
    async_defer = int((scripts or {}).get("con_async_defer", 0) or 0)
    image_count = int((imagenes or {}).get("total", 0) or 0)
    image_state = lighthouse_state("uses-optimized-images", "modern-image-formats", "uses-responsive-images")
    minify_state = lighthouse_state("unminified-javascript", "unminified-css")

    return [
        {"id": 1, "nombre": "Optimización de imágenes", "estado": image_state if image_state != "sin_evidencia" else ("indicio" if image_count else "sin_evidencia"), "evidencia": f"{image_count} imágenes en el HTML; Lighthouse evalúa formato, peso y variantes responsivas." if image_count else "El HTML inicial no contiene etiquetas img.", "requiere": "Lighthouse para medir bytes y variantes descargadas."},
        {"id": 2, "nombre": "Code splitting", "estado": lighthouse_state("unused-javascript", "bootup-time"), "evidencia": "Lighthouse revisa JavaScript sin usar y coste de ejecución; no inspecciona el grafo de módulos del build.", "requiere": "Manifiesto del build para confirmar divisiones y rutas cargadas."},
        {"id": 3, "nombre": "Caché de respuestas API", "estado": "requiere_navegador", "evidencia": "La respuesta HTML no demuestra cómo se cachean las respuestas de API.", "requiere": "Capturar llamadas API del navegador y sus cabeceras de caché."},
        {"id": 4, "nombre": "CDN", "estado": "indicio" if cdn_signals else "sin_evidencia", "evidencia": ("Señales HTTP visibles: " + ", ".join(cdn_signals) + ".") if cdn_signals else "La respuesta no muestra cabeceras comunes de CDN.", "requiere": "Confirmación del proveedor o del DNS para atribuir el CDN."},
        {"id": 5, "nombre": "Minificación de JS y CSS", "estado": minify_state, "evidencia": "Auditorías Lighthouse de JavaScript y CSS sin minificar." if minify_state != "sin_evidencia" else "Sin resultados de Lighthouse para esta comprobación.", "requiere": "PageSpeed Insights."},
        {"id": 6, "nombre": "Índices de base de datos", "estado": "requiere_servidor", "evidencia": "No son observables desde la respuesta pública de la página.", "requiere": "Acceso de solo lectura a métricas o al esquema del servidor."},
        {"id": 7, "nombre": "Renders innecesarios", "estado": "requiere_navegador", "evidencia": "El HTML estático no informa cuántas veces React/Vue vuelve a renderizar componentes.", "requiere": "Perfilado de componentes durante interacciones reproducibles."},
        {"id": 8, "nombre": "Debounce en campos interactivos", "estado": "requiere_navegador", "evidencia": "El HTML no muestra cuántas peticiones genera la escritura del usuario.", "requiere": "Prueba de escritura con captura de solicitudes de red."},
        {"id": 9, "nombre": "Paginación o virtualización", "estado": "requiere_navegador", "evidencia": "La profundidad del crawler no mide listas renderizadas ni el DOM después del scroll.", "requiere": "Inspección del DOM con scroll y conteo de filas renderizadas."},
        {"id": 10, "nombre": "Dependencias JavaScript sin usar", "estado": lighthouse_state("unused-javascript"), "evidencia": "Lighthouse estima bytes de JavaScript sin usar en la página cargada.", "requiere": "Manifiesto del build para identificar paquetes concretos."},
        {"id": 11, "nombre": "Scripts async/defer", "estado": "medido_con_hallazgos" if blocking else "medido", "evidencia": f"{blocking} scripts bloqueantes y {async_defer} scripts con async/defer en el HTML inicial.", "requiere": "Ninguno para la comprobación estática; revisar excepciones en el navegador."},
        {"id": 12, "nombre": "Skeletons de carga", "estado": "requiere_navegador", "evidencia": "El HTML inicial no permite saber qué muestra la interfaz durante una carga lenta.", "requiere": "Capturas de estados de carga con red ralentizada."},
        {"id": 13, "nombre": "Compresión gzip/Brotli", "estado": "medido" if encoding in {"gzip", "br", "zstd"} else "medido_con_hallazgos" if encoding else "sin_evidencia", "evidencia": f"Content-Encoding: {encoding}." if encoding else "No se observó Content-Encoding en la respuesta HTML.", "requiere": "Lighthouse para revisar también CSS, JS y otros recursos."},
        {"id": 14, "nombre": "Balanceador de carga", "estado": "requiere_servidor", "evidencia": "Una respuesta pública no confirma cuántos servidores atienden el sitio.", "requiere": "Información del balanceador o del proveedor de hosting."},
        {"id": 15, "nombre": "Pool de conexiones a base de datos", "estado": "requiere_servidor", "evidencia": "La reutilización de conexiones a la base de datos no aparece en la respuesta HTTP.", "requiere": "Métricas de conexiones del backend o su configuración."},
        {"id": 16, "nombre": "Caché de cálculos costosos", "estado": "requiere_servidor", "evidencia": "La respuesta no revela si los cálculos internos se almacenan en caché.", "requiere": "Trazas o métricas del backend bajo solicitudes repetidas."},
        {"id": 17, "nombre": "Consultas N+1", "estado": "requiere_servidor", "evidencia": "La cantidad de consultas SQL internas no es visible en la página pública.", "requiere": "Trazas SQL/APM para una ruta reproducible."},
        {"id": 18, "nombre": "Caché de servidor", "estado": "indicio" if cache else "sin_evidencia", "evidencia": f"Cache-Control observado: {cache[:180]}." if cache else "No se observó Cache-Control en la respuesta HTML.", "requiere": "La cabecera aporta una señal HTTP; Redis/Varnish u otra caché requieren datos del servidor."},
        {"id": 19, "nombre": "Lighthouse y Core Web Vitals", "estado": "medido" if psi else "sin_evidencia", "evidencia": "PageSpeed Insights aporta Lighthouse y, si hay datos suficientes, métricas de campo CrUX." if psi else "PageSpeed Insights no devolvió resultados para esta URL.", "requiere": "Suficientes muestras CrUX para obtener datos de campo."},
        {"id": 20, "nombre": "Evitar regresiones", "estado": "proceso_interno", "evidencia": "Es un control de calidad del motor y sus correcciones, no una propiedad del sitio auditado.", "requiere": "Pruebas de regresión del analizador y de cada corrección generada."},
    ]
