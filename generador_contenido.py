"""
Generador automatico de contenido para el blog de Web Analyzer.
Cada N horas audita sitios famosos, genera articulo + imagen, y lo publica
en WordPress via REST API. Jetpack lo comparte a Facebook automaticamente.

Uso: python generador_contenido.py
Programable con Cron (Linux) o Programador de Tareas (Windows).
"""

import os
import sys
import json
import hashlib
import time
import random
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)

# =============================================================================
# LOGGING
# =============================================================================

log = logging.getLogger("generador")
log.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
log.addHandler(_handler)
try:
    _fh = logging.FileHandler(Path(__file__).parent / "generador.log", encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(_fh)
except Exception:
    pass


# =============================================================================
# CONFIGURACION
# =============================================================================

ANALYZER_API = "https://web-analyzer-1-l8uc.onrender.com/api/analyze"
WP_URL = os.environ.get("WP_URL", "https://webanalyzer.com.ar/web")
WP_USER = os.environ.get("WP_USER", "a0110133")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", os.getenv("WP_APP_PASSWORD", ""))

# Mapeo de categorias: slug -> ID (actualizar si cambian en WP)
CATEGORIAS = {
    "auditorias": 7,
    "tutoriales": 10,
    "casos-de-exito": 13,
    "seo": 16,
    "rendimiento": 1,
    "wordpress": 1,
    "accesibilidad": 1,
    "conversion": 1,
    "general": 1,
}

OUTPUT_DIR = Path(__file__).parent / "contenido_generado"
OUTPUT_DIR.mkdir(exist_ok=True)

TRACKING_FILE = Path(__file__).parent / "contenido_publicado.json"

MAX_REINTENTOS = 3  # Sitios a probar antes de declarar FALLO


def limpiar_slug(texto):
    """Normaliza un texto para usarlo como slug de WordPress."""
    import unicodedata
    # Normalizar unicode (em dashes, en dashes, etc.)
    texto = unicodedata.normalize("NFKD", texto)
    # Reemplazar caracteres no deseados
    reemplazos = {
        "—": "-", "–": "-", "‒": "-",  # em/en/figure dash
        "‘": "", "’": "", "“": "", "”": "",  # smart quotes
        " ": " ",  # non-breaking space
    }
    for viejo, nuevo in reemplazos.items():
        texto = texto.replace(viejo, nuevo)
    # Solo letras, numeros, espacios y guiones
    import re
    texto = re.sub(r"[^a-zA-Z0-9 ]", "", texto)
    texto = texto.lower().strip()
    texto = re.sub(r"[ ]+", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto.strip("-")


def cargar_tracking():
    """Carga el registro de sitios y posts ya publicados."""
    if TRACKING_FILE.exists():
        try:
            return json.loads(TRACKING_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sitios": [], "educativos": []}


def guardar_tracking(data):
    """Guarda el registro de publicaciones."""
    TRACKING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def elegir_sitio():
    """Elige un sitio que no se haya auditado antes, o el menos repetido."""
    tracking = cargar_tracking()
    usados = tracking.get("sitios", [])
    disponibles = [(url, label) for url, label in SITIOS if url not in usados]
    if not disponibles:
        log.info("Todos los sitios fueron auditados. Reiniciando tracking.")
        tracking["sitios"] = []
        guardar_tracking(tracking)
        disponibles = list(SITIOS)
    return random.choice(disponibles)


def marcar_sitio_usado(url):
    """Registra que un sitio ya fue auditado."""
    tracking = cargar_tracking()
    tracking.setdefault("sitios", []).append(url)
    guardar_tracking(tracking)


def elegir_educativo():
    """Elige un post educativo no publicado, o el mas antiguo."""
    tracking = cargar_tracking()
    usados = tracking.get("educativos", [])
    disponibles = [p for p in POSTS_EDUCATIVOS if p["slug"] not in usados]
    if not disponibles:
        log.info("Todos los posts educativos publicados. Reiniciando tracking.")
        tracking["educativos"] = []
        guardar_tracking(tracking)
        disponibles = list(POSTS_EDUCATIVOS)
    return random.choice(disponibles)


def marcar_educativo_usado(slug):
    """Registra que un post educativo ya fue publicado."""
    tracking = cargar_tracking()
    tracking.setdefault("educativos", []).append(slug)
    guardar_tracking(tracking)

# Sitios para auditar (rotamos, sin bloqueadores de bots)
SITIOS = [
    # Argentina — Deportes
    ("www.cariverplate.com.ar", "River Plate — Sitio Oficial"),
    ("www.bocajuniors.com.ar", "Boca Juniors — Sitio Oficial"),
    ("www.ole.com.ar", "Diario Deportivo Ole"),
    ("www.tycsports.com", "TyC Sports"),
    # Argentina — Noticias
    ("www.infobae.com", "Infobae"),
    ("www.clarin.com", "Clarin"),
    ("www.lanacion.com.ar", "La Nacion"),
    ("www.pagina12.com.ar", "Pagina 12"),
    ("www.cronista.com", "El Cronista"),
    ("www.ambito.com", "Ambito Financiero"),
    # Argentina — Gobierno/Empresas
    ("www.argentina.gob.ar", "Argentina.gob.ar"),
    ("www.mercadolibre.com.ar", "Mercado Libre Argentina"),
    ("www.uade.edu.ar", "UADE"),
    ("www.personal.com.ar", "Personal Argentina"),
    # Latinoamerica
    ("www.uol.com.br", "UOL — Brasil"),
    ("www.mercadolibre.com.mx", "Mercado Libre Mexico"),
    ("www.eluniversal.com.mx", "El Universal — Mexico"),
    ("www.latercera.com", "La Tercera — Chile"),
    ("www.eltiempo.com", "El Tiempo — Colombia"),
    # Internacionales (sitios que permiten auditoria)
    ("www.yahoo.com", "Yahoo"),
    ("one-piece.com", "One Piece — Sitio Oficial"),
    ("www.wikipedia.org", "Wikipedia"),
    ("www.github.com", "GitHub"),
    ("www.stackoverflow.com", "Stack Overflow"),
    ("es.wikipedia.org", "Wikipedia en Espanol"),
    ("www.booking.com", "Booking.com"),
]

# Pares VS para contenido comparativo (Facebook-optimizado)
PARES_VS = [
    (("www.cariverplate.com.ar", "River Plate"), ("www.bocajuniors.com.ar", "Boca Juniors")),
    (("www.ole.com.ar", "Diario Ole"), ("www.tycsports.com", "TyC Sports")),
    (("www.infobae.com", "Infobae"), ("www.clarin.com", "Clarin")),
    (("www.lanacion.com.ar", "La Nacion"), ("www.pagina12.com.ar", "Pagina 12")),
    (("www.mercadolibre.com.ar", "Mercado Libre Argentina"), ("www.mercadolibre.com.mx", "Mercado Libre Mexico")),
    (("www.cronista.com", "El Cronista"), ("www.ambito.com", "Ambito Financiero")),
    (("www.wikipedia.org", "Wikipedia"), ("es.wikipedia.org", "Wikipedia en Espanol")),
    (("www.uol.com.br", "UOL Brasil"), ("www.eltiempo.com", "El Tiempo Colombia")),
    (("www.latercera.com", "La Tercera Chile"), ("www.eluniversal.com.mx", "El Universal Mexico")),
]

# Plantillas de titulos
TITULOS = [
    "Auditamos {label}: saco {promedio}/10 — ¿y tu sitio?",
    "{label} obtuvo {promedio}/10 en nuestra auditoria web",
    "¿{label} pierde clientes? Análisis completo: {promedio}/10",
    "Scorecard de {label}: {promedio} de 10. ¿El tuyo esta mejor?",
    "Analizamos el sitio de {label} — resultados sorprendentes",
]

# Plantillas de titulos VS
TITULOS_VS = [
    "{label1} vs {label2}: que sitio esta mejor optimizado?",
    "Cara a cara: auditamos {label1} y {label2} -- el resultado te va a sorprender",
    "{label1} vs {label2}: la batalla por el mejor sitio web",
    "Quien gana? {label1} vs {label2} -- auditoria completa",
    "Duelo de gigantes: {label1} contra {label2} -- cual tiene mejor web?",
]
# Posts educativos (sin auditoria, solo contenido)
POSTS_EDUCATIVOS = [
    # === SEO ===

    {
        "titulo": "5 errores que matan el SEO de tu web (y como arreglarlos)",
        "slug": "5-errores-seo-web",
        "categoria": "SEO",
        "cuerpo": """<p>Todos los sitios tienen errores. Incluso los mas grandes. Estos son los 5 que mas vemos en nuestras auditorias:</p>
<h3>1. Meta description vacia o muy larga</h3><p>Google muestra lo que quiere si no le das una description clara de 120-155 caracteres.</p>
<h3>2. Sin Open Graph tags</h3><p>Cuando compartis en WhatsApp o redes sociales no sale imagen ni descripcion. Perdes clicks.</p>
<h3>3. Imagenes sin alt text</h3><p>Google no entiende las imagenes. Y los lectores de pantalla tampoco.</p>
<h3>4. Sin lazy loading</h3><p>Todas las imagenes cargan juntas. Tu pagina tarda segundos extra por cada foto invisible.</p>
<h3>5. Title muy corto o muy largo</h3><p>Entre 40 y 60 caracteres. Fuera de eso, Google recorta o ignora.</p>
<p><strong>¿Cuantos tiene tu sitio?</strong> <a href='https://web-analyzer-1-l8uc.onrender.com/'>Auditalo gratis en 30 segundos →</a></p>""",
    },
    {
        "titulo": "Que son los Core Web Vitals y por que Google los exige",
        "slug": "core-web-vitals-google",
        "categoria": "SEO",
        "cuerpo": """<p>Desde 2021 Google usa los Core Web Vitals como factor de ranking. Si tu sitio no pasa, perdes posiciones.</p>
<h3>LCP (Largest Contentful Paint)</h3><p>El contenido principal debe cargar en menos de 2.5 segundos. Si tu imagen hero tarda 6 segundos, Google te castiga.</p>
<h3>INP (Interaction to Next Paint)</h3><p>Que tan rapido responde tu pagina cuando el usuario hace clic. Menos de 200ms es bueno. Mas de 500ms es pobre.</p>
<h3>CLS (Cumulative Layout Shift)</h3><p>Que las cosas no se muevan mientras cargan. ¿Viste cuando vas a tocar un boton y se mueve porque cargo una imagen? Eso es CLS.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Medi tus Core Web Vitals gratis →</a></p>""",
    },
    {
        "titulo": "Schema markup: que es y por que tu web lo necesita",
        "slug": "schema-markup-web",
        "categoria": "SEO",
        "cuerpo": """<p>El 80% de los sitios que auditamos no tiene datos estructurados. Es invisible para los rich snippets de Google.</p>
<h3>¿Que es schema markup?</h3><p>Es un formato de datos (JSON-LD) que le dice a Google exactamente que hay en tu pagina: un articulo, un producto, un evento, una receta.</p>
<h3>¿Para que sirve?</h3><p>Para que Google muestre estrellitas, precios, fechas de eventos y preguntas frecuentes directamente en los resultados de busqueda. Mas clicks, mas trafico.</p>
<h3>¿Como implementarlo?</h3><p>Con plugins como Yoast SEO o Rank Math en WordPress, o agregando el script JSON-LD manualmente en el header.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tu sitio tiene schema? Auditalo →</a></p>""",
    },
    {
        "titulo": "SEO local: como aparecer en Google cuando buscan tu negocio",
        "slug": "seo-local-google-negocio",
        "categoria": "SEO",
        "cuerpo": """<p>El 46% de las busquedas en Google tiene intencion local. Si no trabajaste tu SEO local, no existis para tus vecinos.</p>
<h3>Google Business Profile</h3><p>Crea y completa tu perfil. Direccion, telefono, horarios, fotos. Responde las resenas. Es gratis y es lo primero que ve la gente.</p>
<h3>Consistencia NAP</h3><p>Name, Address, Phone. Debe ser identico en tu sitio, Google, redes sociales y directorios. Cualquier diferencia confunde a Google.</p>
<h3>Pagina de contacto</h3><p>Con mapa embebido, telefono cliqueable, formulario. No solo un email.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita el SEO de tu negocio →</a></p>""",
    },
    # === Rendimiento ===
    {
        "titulo": "¿Por que los sitios grandes tienen puntajes bajos en rendimiento?",
        "slug": "sitios-grandes-rendimiento-bajo",
        "categoria": "Rendimiento",
        "cuerpo": """<p>Auditamos sitios con millones de visitas. La mayoria no pasa de 6/10. ¿Por que?</p>
<h3>Demasiados scripts de terceros</h3><p>Anuncios, tracking, analytics, widgets... cada uno suma carga.</p>
<h3>Imagenes sin optimizar</h3><p>Suben fotos directo de la camara. Sin compresion, sin WebP, sin lazy loading.</p>
<h3>Prioridad al contenido visual</h3><p>Prefieren que se vea lindo a que cargue rapido. El visitante espera.</p>
<h3>Nadie les muestra el problema</h3><p>No tienen un auditor que les diga "esto esta mal". Hasta que llega alguien con Web Analyzer.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tu sitio tambien? Analizalo gratis →</a></p>""",
    },
    {
        "titulo": "WebP: el formato de imagen que acelera tu sitio al instante",
        "slug": "webp-imagenes-acelerar-sitio",
        "categoria": "Rendimiento",
        "cuerpo": """<p>Convertir tus imagenes a WebP puede reducir su peso a la mitad sin perder calidad. Es lo mas rapido que podes hacer para acelerar tu web.</p>
<h3>¿Que es WebP?</h3><p>Un formato de imagen desarrollado por Google. Comprime mejor que JPEG y PNG manteniendo la misma calidad visual.</p>
<h3>Numeros reales</h3><p>Una foto de 800KB en JPEG puede pesar 300KB en WebP. En una pagina con 10 fotos, bajas de 8MB a 3MB. Tu pagina carga en la mitad de tiempo.</p>
<h3>Como usarlo</h3><p>Plugins como WebP Express o ShortPixel convierten tus imagenes automaticamente. Si usas WordPress, es 1 clic.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tus imagenes estan optimizadas? Auditalo →</a></p>""",
    },
    {
        "titulo": "JavaScript bloqueante: el asesino silencioso de tu velocidad",
        "slug": "javascript-bloqueante-rendimiento",
        "categoria": "Rendimiento",
        "cuerpo": """<p>Un solo script mal puesto puede retrasar la carga de tu pagina 3 o 4 segundos.</p>
<h3>¿Que es el render-blocking?</h3><p>Cuando un script se carga antes que el contenido visible. El navegador frena todo hasta que ese script se descarga y ejecuta. Mientras tanto, tu visitante ve una pantalla en blanco.</p>
<h3>Como detectarlo</h3><p>En Web Analyzer te marcamos cada script que bloquea el renderizado. La mayoria son widgets de redes sociales, chatbots y trackers de marketing.</p>
<h3>Solucion</h3><p>Mover scripts al footer, usar atributos async o defer, o eliminar los que no aportan valor real.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Encontra tus scripts bloqueantes →</a></p>""",
    },
    {
        "titulo": "Cache y CDN: las 2 herramientas que toda web deberia usar",
        "slug": "cache-cdn-herramientas-web",
        "categoria": "Rendimiento",
        "cuerpo": """<p>El cache guarda una copia rapida de tu pagina. El CDN la distribuye por el mundo. Juntos hacen magia.</p>
<h3>Cache de navegador</h3><p>Le dice al visitante "no descargues esto de nuevo, ya lo tenes". Imagenes, CSS y fuentes se cargan instantaneo en la segunda visita.</p>
<h3>Cache de servidor</h3><p>Guarda la pagina ya generada. En vez de construirla cada vez (PHP + base de datos), la entrega lista. WP Rocket y Litespeed lo hacen.</p>
<h3>CDN (Content Delivery Network)</h3><p>Tus archivos se copian a servidores en todo el mundo. Un visitante de Japon recibe tu pagina desde un servidor en Asia, no desde Argentina. Cloudflare tiene plan gratuito.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tu sitio usa cache? Auditalo →</a></p>""",
    },
    # === WordPress ===
    {
        "titulo": "WordPress lento: 4 soluciones que aplicamos y funcionan",
        "slug": "wordpress-lento-soluciones",
        "categoria": "WordPress",
        "cuerpo": """<p>Tenemos 3 sitios WordPress que pasaron de ~5.5 a 9.6/10. Esto fue lo que hicimos:</p>
<h3>1. Activar lazy loading</h3><p>Las imagenes cargan solo cuando el usuario las va a ver. WP Rocket o Litespeed lo hacen en 1 clic.</p>
<h3>2. Convertir imagenes a WebP</h3><p>Pesan la mitad que JPG o PNG con la misma calidad. Plugins gratuitos como WebP Express lo automatizan.</p>
<h3>3. Completar meta tags</h3><p>Title, description, Open Graph. Yoast SEO o Rank Math lo manejan.</p>
<h3>4. Alt text en todas las imagenes</h3><p>Descriptivo, util, sin keyword stuffing. Cada imagen deberia describirse en una frase.</p>
<p><strong>Resultado:</strong> paginas que cargan en menos de 1 segundo, mejor posicion en Google, y mas conversion.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita tu WordPress y recibi las soluciones →</a></p>""",
    },
    {
        "titulo": "Plugins de WordPress: menos es mas",
        "slug": "plugins-wordpress-menos-es-mas",
        "categoria": "WordPress",
        "cuerpo": """<p>Cada plugin suma peso, consultas a la base de datos y posibles vulnerabilidades. La mayoria de los sitios que auditamos tiene el doble de plugins necesarios.</p>
<h3>El problema</h3><p>Cada plugin carga sus propios CSS y JS en todas las paginas, incluso donde no se usa. 20 plugins pueden significar 40 archivos extra que el visitante tiene que descargar.</p>
<h3>La solucion</h3><p>Audita tus plugins cada 3 meses. Si un plugin no se uso en el ultimo mes, eliminalo. Busca plugins que hagan varias cosas en vez de instalar uno por funcion.</p>
<h3>Plugins esenciales</h3><p>1 de cache (WP Rocket o Litespeed), 1 de SEO (Yoast o Rank Math), 1 de seguridad (Wordfence). El resto, solo si realmente lo necesitas.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita el rendimiento de tu WordPress →</a></p>""",
    },
    {
        "titulo": "Por que tu WordPress deberia usar un tema liviano",
        "slug": "wordpress-tema-liviano",
        "categoria": "WordPress",
        "cuerpo": """<p>Los temas "todo en uno" con builders visuales son los que mas lentitud generan en WordPress.</p>
<h3>El peso de los temas pesados</h3><p>Temas como Avada o Divi cargan cientos de KB en CSS y JS aunque solo uses el 10% de sus funciones. El resultado: paginas que tardan 5+ segundos en cargar.</p>
<h3>Alternativas livianas</h3><p>GeneratePress, Astra, Kadence, o los temas nativos de WordPress (Twenty Twenty-Five). Todos pesan menos de 50KB y son igual de flexibles.</p>
<h3>¿Y si ya tengo un tema pesado?</h3><p>Desactiva los modulos que no uses. No cargues Font Awesome entero si solo usas 3 iconos. Desactiva las animaciones que solo suman carga.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tu tema esta frenando tu web? Auditalo →</a></p>""",
    },
    # === Accesibilidad ===
    {
        "titulo": "Accesibilidad web: ¿tu sitio puede usarlo una persona ciega?",
        "slug": "accesibilidad-web-auditoria",
        "categoria": "Accesibilidad",
        "cuerpo": """<p>El 99% de los sitios que auditamos falla en accesibilidad. No es un detalle: es exclusion.</p>
<h3>Lo que siempre falta:</h3><p>Atributos alt en imagenes, labels en formularios, estructura de headings correcta (H1, H2, H3...), contraste de colores suficiente.</p>
<h3>¿A quien afecta?</h3><p>Personas ciegas o con baja vision que usan lectores de pantalla. En Argentina son mas de 1 millon de personas.</p>
<h3>¿Es obligatorio?</h3><p>En muchos paises si (WCAG 2.1). En Argentina la ley de accesibilidad web aplica a sitios publicos, pero es buena practica para todos.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita la accesibilidad de tu sitio gratis →</a></p>""",
    },
    {
        "titulo": "Formularios accesibles: no pierdas clientes por un input roto",
        "slug": "formularios-accesibles-web",
        "categoria": "Accesibilidad",
        "cuerpo": """<p>Cada formulario sin label es un cliente que no puede completarlo. Pasa mas seguido de lo que crees.</p>
<h3>El error mas comun</h3><p>Usar placeholder en vez de label. El placeholder desaparece cuando empezas a escribir. Un lector de pantalla no lo lee. Una persona mayor no recuerda que iba en ese campo.</p>
<h3>La solucion</h3><p>Cada input necesita su label vinculado con el atributo for. Siempre visible, siempre claro. El placeholder es ayuda extra, no reemplazo del label.</p>
<h3>Estados de error</h3><p>Si el usuario se equivoca, mostrale el error junto al campo, en texto, no solo con color rojo. Y decile exactamente como corregirlo.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Revisa la accesibilidad de tus formularios →</a></p>""",
    },
    {
        "titulo": "Contraste de colores: el error invisible que ahuyenta usuarios",
        "slug": "contraste-colores-accesibilidad",
        "categoria": "Accesibilidad",
        "cuerpo": """<p>Texto gris claro sobre fondo blanco. ¿Cuantas veces lo viste? Elegante, si. Legible, no.</p>
<h3>La regla WCAG</h3><p>El texto normal necesita un contraste minimo de 4.5:1 contra el fondo. El texto grande (18px+) necesita 3:1. La mayoria de los grises claros no llegan.</p>
<h3>A quien afecta</h3><p>Personas con baja vision, daltonismo, o simplemente alguien mirando el celular al sol. No es un nicho: es el 10% de tus visitantes.</p>
<h3>Como medirlo</h3><p>WebAIM tiene un Contrast Checker gratuito. Web Analyzer detecta automaticamente los contrastes bajos en tu sitio.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita el contraste de tu web →</a></p>""",
    },
    # === Conversion ===
    {
        "titulo": "Como capturar emails de los visitantes que se van sin comprar",
        "slug": "capturar-emails-visitantes",
        "categoria": "Conversion",
        "cuerpo": """<p>La mayoria de los sitios que auditamos no tiene formulario de captura de emails. Estan regalando trafico.</p>
<h3>El dato que duele:</h3><p>Menos del 3% de los visitantes compra en la primera visita. Sin email, perdiste al otro 97% para siempre.</p>
<h3>Lo que funciona:</h3><p>Un formulario simple: 1 campo (email) + 1 boton. Ofrece algo a cambio: "Recibi las ofertas", "Guia gratuita", "Tips semanales".</p>
<h3>Donde ponerlo:</h3><p>Al final del contenido, en la barra lateral, o como popup con salida (exit intent).</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tu sitio captura emails? Auditalo gratis →</a></p>""",
    },
    {
        "titulo": "La velocidad de tu sitio afecta tus ventas (y tenemos los numeros)",
        "slug": "velocidad-sitio-ventas-numeros",
        "categoria": "Conversion",
        "cuerpo": """<p>Cada segundo extra de carga reduce la conversion un 7% en promedio. Si tu pagina tarda 5 segundos, perdiste un 28% de ventas.</p>
<h3>Datos reales</h3><p>Amazon calculo que 100ms de demora les costaba un 1% en ventas. Google descubrio que 500ms extra reducian el trafico un 20%. No es teoria: es plata.</p>
<h3>Mobile es peor</h3><p>El 53% de los visitantes abandona un sitio movil si tarda mas de 3 segundos en cargar. Y el 60% de tu trafico probablemente sea movil.</p>
<h3>Que hacer</h3><p>Medi tu velocidad hoy. El 80% de los problemas se arreglan con lazy loading, WebP y cache.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Medi la velocidad de tu sitio →</a></p>""",
    },
    {
        "titulo": "Call-to-action: como escribir botones que la gente aprieta",
        "slug": "call-to-action-botones-efectivos",
        "categoria": "Conversion",
        "cuerpo": """<p>"Enviar", "Aceptar", "Click aqui". Si tus botones dicen eso, estas perdiendo conversiones.</p>
<h3>Lo que no funciona</h3><p>Verbos genericos. La gente no quiere "enviar", quiere lo que pasa despues de enviar: "Recibir la guia", "Empezar ahora", "Ver precios".</p>
<h3>Lo que si funciona</h3><p>Botones especificos, con beneficio claro, que empiezan con verbo. "Analizar mi sitio gratis", "Descargar soluciones", "Quiero mi auditoria".</p>
<h3>Color y posicion</h3><p>Un solo color de accion (contraste alto contra el fondo). Arriba del pliegue. Repetilo al final de la pagina. No le hagas pensar al visitante donde hacer clic.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita la conversion de tu web →</a></p>""",
    },
    # === Seguridad ===
    {
        "titulo": "HTTPS: si tu sitio no tiene candado, perdes visitantes",
        "slug": "https-candado-sitio-seguro",
        "categoria": "SEO",
        "cuerpo": """<p>Google marca como "No segura" a toda pagina que carga en HTTP. Tus visitantes lo ven apenas entran.</p>
<h3>Que pasa sin HTTPS</h3><p>El navegador muestra un triangulo de advertencia. Los datos del formulario viajan sin encriptar. Google te baja en el ranking. Los navegadores modernos directamente bloquean algunas funciones.</p>
<h3>Como activarlo</h3><p>Let's Encrypt ofrece certificados SSL gratuitos. La mayoria de los hostings (incluido Ferozo) lo activan con 1 clic desde el panel de control.</p>
<h3>Despues de activarlo</h3><p>Redirigi todo el trafico HTTP a HTTPS. Actualiza las URLs internas. Verifica que no tengas contenido mixto (imagenes o scripts en HTTP dentro de una pagina HTTPS).</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Verifica la seguridad de tu sitio →</a></p>""",
    },
    {
        "titulo": "Copias de seguridad: la unica cosa que te separa del desastre",
        "slug": "copias-seguridad-wordpress",
        "categoria": "WordPress",
        "cuerpo": """<p>Un hackeo, un update fallido, un error humano. Sin backup, perdiste todo. Y la mayoria de los sitios no tiene backups automaticos.</p>
<h3>Regla de oro: 3-2-1</h3><p>3 copias, en 2 medios distintos, 1 fuera del sitio. Por ejemplo: backup en el hosting + backup en Google Drive.</p>
<h3>Como hacerlo en WordPress</h3><p>UpdraftPlus (gratis) programa backups automaticos a Google Drive, Dropbox o email. En 10 minutos queda configurado para siempre.</p>
<h3>Cada cuanto</h3><p>Backup diario si publicas seguido. Semanal si es un sitio institucional. Siempre antes de actualizar WordPress o plugins.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita la seguridad de tu WordPress →</a></p>""",
    },
    # === Mobile ===
    {
        "titulo": "Mobile-first: si tu sitio no funciona en el celular, no existe",
        "slug": "mobile-first-sitio-celular",
        "categoria": "Rendimiento",
        "cuerpo": """<p>Google usa la version movil de tu sitio para decidir tu posicion en los resultados. No importa que tan linda sea la version de escritorio.</p>
<h3>Los numeros</h3><p>El 60% del trafico web mundial es movil. En Argentina, mas del 70%. Si tu pagina no se adapta bien a pantallas chicas, 7 de cada 10 visitantes se van.</p>
<h3>Errores comunes</h3><p>Texto muy chico (menos de 16px), botones muy juntos (menos de 8mm), contenido mas ancho que la pantalla (scroll horizontal), popups que no se pueden cerrar.</p>
<h3>Como probarlo</h3><p>Achica la ventana del navegador. O mejor: abri tu sitio en tu celular. ¿Tenes que hacer zoom para leer? ¿Los botones se tocan facil? ¿El formulario es usable con una mano?</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>Audita la version movil de tu sitio →</a></p>""",
    },
    {
        "titulo": "Imagenes responsive: una imagen para cada pantalla",
        "slug": "imagenes-responsive-srcset",
        "categoria": "Rendimiento",
        "cuerpo": """<p>Cargar una imagen de 2000px de ancho en un celular de 375px es desperdiciar el 80% del ancho de banda. Tus visitantes lo notan.</p>
<h3>El atributo srcset</h3><p>HTML permite definir varias versiones de la misma imagen para distintos tamanos de pantalla. El navegador elige la que necesita, no la mas grande.</p>
<h3>Cuanto ahorra</h3><p>Una foto de hero que pesa 400KB en desktop puede pesar 80KB en mobile con las mismas proporciones. En una galeria de 20 fotos, ahorras mas de 6MB de descarga.</p>
<h3>Como implementarlo</h3><p>WordPress ya genera versiones en distintos tamanos automaticamente. Solo necesitas que tu tema use srcset en vez de img simple.</p>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/'>¿Tus imagenes son responsive? Auditalo →</a></p>""",
    },
]

# =============================================================================
# Imagenes (Pillow) — Mockup profesional de Web Analyzer
# =============================================================================

W, H = 1200, 630  # Ratio Facebook/WhatsApp 1.91:1

# Paleta Web Analyzer (inspirada en la landing real)
WHITE = (255, 255, 255)
BG_WARM = (248, 245, 240)        # Fondo crema claro
BG_CARD = (255, 255, 255)        # Cards blancas
SURFACE = (240, 242, 245)        # Superficie gris claro
BORDER_CARD = (208, 215, 222)    # Borde sutil
TEXT_DARK = (13, 17, 23)         # Casi negro
TEXT_BODY = (87, 96, 106)        # Gris medio
TEXT_MUTED = (140, 148, 158)     # Gris claro
BLUE = (31, 111, 235)            # Azul marca (#1f6feb)
BLUE_LIGHT = (88, 166, 255)      # Azul claro
GREEN = (63, 185, 80)            # Verde éxito
YELLOW = (210, 153, 34)          # Amarillo advertencia
RED = (248, 81, 73)              # Rojo problema
BROWSER_BG = (36, 41, 47)        # Barra de navegador

FONT_B = None
FONT_R = None
for p in [
    "C:\\Windows\\Fonts\\segoeuib.ttf",
    "C:\\Windows\\Fonts\\segoeui.ttf",
    "C:\\Windows\\Fonts\\arialbd.ttf",
    "C:\\Windows\\Fonts\\arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]:
    if os.path.exists(p):
        if FONT_B is None:
            FONT_B = p
        elif FONT_R is None:
            FONT_R = p
if not FONT_R:
    FONT_R = FONT_B
if not FONT_B:
    FONT_B = FONT_R = "arial.ttf"


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT_R, size)
    except Exception:
        return ImageFont.load_default()


def color_score(s):
    if s >= 8:
        return GREEN
    if s >= 5:
        return YELLOW
    return RED


def texto_centrado(draw, text, y, f, color):
    bbox = draw.textbbox((0, 0), text, font=f)
    draw.text(((W - bbox[2] + bbox[0]) / 2, y), text, fill=color, font=f)


def texto_ancho(draw, text, x, y, f, color):
    draw.text((x, y), text, fill=color, font=f)


def texto_bbox(draw, text, f):
    bbox = draw.textbbox((0, 0), text, font=f)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _recortar_texto(draw, text, max_w, f):
    """Recorta texto con '...' si excede el ancho maximo."""
    if texto_bbox(draw, text, f)[0] <= max_w:
        return text
    for i in range(len(text), 0, -1):
        t = text[:i] + "..."
        if texto_bbox(draw, t, f)[0] <= max_w:
            return t
    return text[:3] + "..."


def generar_imagen_mockup(sitio, label, promedio, scores, path, es_educativo=False, categoria=""):
    """
    Genera una imagen 1200x630 que simula la interfaz de Web Analyzer:
    - Barra de navegador con URL
    - Header con branding
    - Scorecard con puntaje y categorias
    - CTA al final
    """
    img = Image.new("RGB", (W, H), BG_WARM)
    draw = ImageDraw.Draw(img)

    # -----------------------------------------------------------------------
    # Barra de navegador (top) — simula una ventana de Chrome
    # -----------------------------------------------------------------------
    draw.rectangle([0, 0, W, 38], fill=BROWSER_BG)
    # Botones de ventana
    for bx, bc in [(20, (255, 95, 86)), (42, (255, 189, 46)), (64, (39, 201, 63))]:
        draw.ellipse([bx, 12, bx + 12, 24], fill=bc)
    # Barra URL
    url_bar_x, url_bar_w = 100, W - 160
    draw.rectangle([url_bar_x, 8, url_bar_x + url_bar_w, 30], fill=(50, 55, 61))
    draw.rounded_rectangle([url_bar_x, 8, url_bar_x + url_bar_w, 30], radius=6, fill=(50, 55, 61))
    url_display = _recortar_texto(draw, f"https://webanalyzer.com.ar/?url={sitio}", url_bar_w - 20, font(13, False))
    draw.text((url_bar_x + 14, 15), url_display, fill=(200, 205, 210), font=font(13, False))

    # -----------------------------------------------------------------------
    # Header — WebAnalyzer branding
    # -----------------------------------------------------------------------
    y = 56
    draw.text((40, y), "Web", fill=TEXT_DARK, font=font(27, True))
    draw.text((40 + texto_bbox(draw, "Web", font(27, True))[0], y), "Analyzer", fill=BLUE, font=font(27, True))
    draw.text((40, y + 30), "& Optimizer", fill=TEXT_BODY, font=font(14, False))
    # Tag "AUDITORIA GRATIS" o categoria
    tag_text = categoria.upper() if es_educativo else "AUDITORIA GRATIS"
    tag_color = {"SEO": YELLOW, "RENDIMIENTO": RED, "WORDPRESS": BLUE, "ACCESIBILIDAD": GREEN, "CONVERSION": BLUE}.get(tag_text, BLUE)
    tag_w = texto_bbox(draw, tag_text, font(12, True))[0] + 20
    draw.rounded_rectangle([W - 200 - tag_w, y + 2, W - 200, y + 24], radius=4, fill=tag_color)
    draw.text((W - 200 - tag_w + 10, y + 6), tag_text, fill=WHITE, font=font(12, True))

    # -----------------------------------------------------------------------
    # Hero / Titulo principal
    # -----------------------------------------------------------------------
    y = 120
    if es_educativo:
        # Wrap del titulo largo
        palabras = label.split()
        lineas = []
        linea_actual = ""
        f_titulo = font(28, True)
        for p in palabras:
            test = (linea_actual + " " + p).strip()
            if texto_bbox(draw, test, f_titulo)[0] < W - 80:
                linea_actual = test
            else:
                lineas.append(linea_actual)
                linea_actual = p
        if linea_actual:
            lineas.append(linea_actual)
        for l in lineas:
            draw.text((40, y), l, fill=TEXT_DARK, font=f_titulo)
            y += 40
    else:
        draw.text((40, y), "Auditamos", fill=TEXT_DARK, font=font(28, True))
        draw.text((40 + texto_bbox(draw, "Auditamos", font(28, True))[0] + 12, y), label, fill=BLUE, font=font(28, True))
        y += 36
        draw.text((40, y), "Resultados reales del analisis automatico en 5 categorias.", fill=TEXT_BODY, font=font(16, False))

    # -----------------------------------------------------------------------
    # Scorecard — tarjeta blanca con sombra
    # -----------------------------------------------------------------------
    card_y = 210 if not es_educativo else max(y + 16, 210)
    card_h = 260
    # Sombra (rectangulo desplazado)
    draw.rectangle([44, card_y + 4, W - 44, card_y + card_h + 4], fill=(220, 215, 210))
    # Card blanca
    draw.rounded_rectangle([40, card_y, W - 40, card_y + card_h], radius=12, fill=BG_CARD, outline=BORDER_CARD, width=1)

    if es_educativo:
        # Educativo: icono grande + texto explicativo
        iconos = {"SEO": "🔍", "Rendimiento": "⚡", "WordPress": "🔧", "Accesibilidad": "♿", "Conversion": "📈"}
        icono = iconos.get(categoria, "💡")
        draw.text((80, card_y + 30), icono, fill=TEXT_DARK, font=font(48, True))
        draw.text((80, card_y + 100), "Web Analyzer", fill=TEXT_DARK, font=font(24, True))
        draw.text((80, card_y + 130), "Auditoria automatica • 5 categorias • 30 segundos", fill=TEXT_BODY, font=font(15, False))
        draw.text((80, card_y + 165), "Sin registro. Gratis. Resultados instantaneos.", fill=TEXT_MUTED, font=font(14, False))
        # Preview de scorecard
        preview_x = 500
        preview_cats = ["SEO", "Rendimiento", "Accesibilidad", "Conversion"]
        preview_scores = [8.5, 6.2, 7.8, 5.5]
        for i, (cn, cs) in enumerate(zip(preview_cats, preview_scores)):
            cx = preview_x + i * 150
            cc = color_score(cs)
            draw.rounded_rectangle([cx, card_y + 30, cx + 130, card_y + 200], radius=8, fill=SURFACE, outline=BORDER_CARD, width=1)
            texto_centrado(draw, cn, card_y + 55, font(14, True), TEXT_BODY)
            c_score = font(42, True)
            sw = texto_bbox(draw, str(cs), c_score)[0]
            draw.text((cx + 65 - sw / 2, card_y + 90), str(cs), fill=cc, font=c_score)
            texto_centrado(draw, "/10", card_y + 140, font(12, False), TEXT_MUTED)
    else:
        # Auditoria: score grande a la izquierda + categorias en grid
        # Circulo de puntaje
        scx, scy = 105, card_y + card_h // 2
        sr = 72
        pc = color_score(promedio)
        draw.ellipse([scx - sr, scy - sr, scx + sr, scy + sr], fill=pc)
        # Texto del score
        stxt = str(promedio)
        f_s = font(64, True)
        sw, sh = texto_bbox(draw, stxt, f_s)
        draw.text((scx - sw / 2, scy - sh / 2 - 6), stxt, fill=WHITE, font=f_s)
        f_s10 = font(15, False)
        draw.text((scx + sr - 30, scy - 14), "/10", fill=WHITE, font=f_s10)
        # Label bajo el circulo
        draw.text((scx - texto_bbox(draw, "PUNTAJE", font(11, True))[0] / 2, scy + sr + 10), "PUNTAJE", fill=TEXT_MUTED, font=font(11, True))

        # Categorias a la derecha del score
        cats = list(scores.keys())
        n_cats = min(len(cats), 5)
        grid_x = 210
        grid_w = W - grid_x - 60
        col_gap = 12
        card_w = (grid_w - (n_cats - 1) * col_gap) / n_cats
        for i in range(n_cats):
            cat = cats[i]
            s = scores[cat]
            c = color_score(s)
            cx = grid_x + i * (card_w + col_gap)
            # Tarjeta de categoria
            draw.rounded_rectangle([cx, card_y + 30, cx + card_w, card_y + card_h - 30], radius=8, fill=SURFACE, outline=BORDER_CARD, width=1)
            # Nombre de categoria
            cat_display = cat[:14]  # truncar si es muy largo
            texto_centrado(draw, cat_display, card_y + 50, font(13, True), TEXT_BODY)
            # Score
            f_cs = font(38, True)
            ssw = texto_bbox(draw, str(s), f_cs)[0]
            draw.text((cx + card_w / 2 - ssw / 2, card_y + 82), str(s), fill=c, font=f_cs)
            texto_centrado(draw, "/10", card_y + 130, font(12, False), TEXT_MUTED)
            # Barras de progreso
            bar_y = card_y + 170
            bar_w = card_w - 24
            draw.rectangle([cx + 12, bar_y, cx + 12 + bar_w, bar_y + 6], fill=(220, 215, 210))
            fill_w = int(bar_w * s / 10)
            if fill_w > 0:
                draw.rectangle([cx + 12, bar_y, cx + 12 + fill_w, bar_y + 6], fill=c)

    # -----------------------------------------------------------------------
    # Footer — CTA
    # -----------------------------------------------------------------------
    footer_y = card_y + card_h + 24
    # Linea separadora
    draw.line([40, footer_y, W - 40, footer_y], fill=BORDER_CARD, width=1)
    footer_y += 16
    draw.text((40, footer_y), "Analiza tu sitio gratis en 30 segundos", fill=TEXT_BODY, font=font(17, False))
    draw.text((40, footer_y + 24), "webanalyzer.com.ar", fill=BLUE, font=font(15, True))
    # Boton CTA
    btn_text = "Analizar gratis →"
    btn_w = texto_bbox(draw, btn_text, font(16, True))[0] + 40
    draw.rounded_rectangle([W - 60 - btn_w, footer_y - 2, W - 60, footer_y + 36], radius=8, fill=BLUE)
    draw.text((W - 60 - btn_w + 20, footer_y + 4), btn_text, fill=WHITE, font=font(16, True))

    img.save(path, quality=95)
    return path


def generar_imagen_scorecard(sitio, label, promedio, scores, path):
    return generar_imagen_mockup(sitio, label, promedio, scores, path, es_educativo=False)


def generar_imagen_educativa(titulo, categoria, path):
    return generar_imagen_mockup("", titulo, 0, {}, path, es_educativo=True, categoria=categoria)


# =============================================================================
# WordPress REST API
# =============================================================================

def wp_publicar(titulo, cuerpo, slug, imagen_path=None, categoria="general"):
    """Publica un post en WordPress via REST API. Retorna URL o None."""
    if not WP_URL or not WP_USER or not WP_APP_PASSWORD:
        log.warning(f"WP no configurado. Post: {titulo[:60]}...")
        return None

    api = WP_URL.rstrip("/") + "/wp-json/wp/v2"
    cat_id = CATEGORIAS.get(categoria.lower().replace(" ", "-"), 1)

    try:
        # Subir imagen primero (si hay)
        imagen_id = None
        if imagen_path and os.path.exists(imagen_path):
            import base64
            filename = os.path.basename(imagen_path)
            with open(imagen_path, "rb") as f:
                img_data = f.read()

            resp = requests.post(
                f"{api}/media",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Type": "image/png",
                },
                data=img_data,
                auth=(WP_USER, WP_APP_PASSWORD),
                timeout=30,
            )
            if resp.status_code == 201:
                imagen_id = resp.json().get("id")
                log.info(f"  Imagen subida: ID {imagen_id}")
            else:
                log.warning(f"  Imagen no subida ({resp.status_code}): {resp.text[:200]}")

        # Crear post
        post_data = {
            "title": titulo,
            "content": cuerpo,
            "slug": slug,
            "status": "publish",
            "categories": [cat_id],
        }
        if imagen_id:
            post_data["featured_media"] = imagen_id

        resp = requests.post(
            f"{api}/posts",
            json=post_data,
            auth=(WP_USER, WP_APP_PASSWORD),
            timeout=30,
        )
        if resp.status_code == 201:
            data = resp.json()
            log.info(f"  Publicado: {data.get('link', '?')}")
            return data.get("link")
        else:
            log.error(f"  WP devolvio {resp.status_code}: {resp.text[:300]}")
            return None

    except Exception as e:
        log.error(f"  WP request: {e}")
        return None


# =============================================================================
# Generadores de posts
# =============================================================================

def generar_post_auditoria():
    """Audita un sitio aleatorio y genera post + imagen. Reintenta hasta MAX_REINTENTOS."""
    for intento in range(1, MAX_REINTENTOS + 1):
        url, label = elegir_sitio()
        log.info(f"Intento {intento}/{MAX_REINTENTOS}: auditando {url} ({label})")

        # Auditar
        try:
            resp = requests.post(
                ANALYZER_API,
                json={"url": url, "depth": 1},
                timeout=90,
            )
            data = resp.json()
        except Exception as e:
            log.warning(f"  Fallo la auditoria (intento {intento}): {e}")
            continue

        if data.get("errores"):
            log.warning(f"  API devolvio error: {data['errores'][0]}")
            continue

        promedio = data.get("promedio", 0)
        scores_raw = data.get("scorecard", {})

        if not scores_raw or promedio == 0:
            log.warning(f"  Sin datos de scorecard (intento {intento})")
            continue

        # Extraer scores simplificados
        scores = {}
        for cat, info in scores_raw.items():
            puntaje = info.get("puntaje", 0) if isinstance(info, dict) else info[0]
            scores[cat] = puntaje

        if not scores:
            log.warning(f"  Scorecard vacio (intento {intento})")
            continue

        log.info(f"  Promedio: {promedio}/10 | Categorias: {len(scores)}")

        # Generar imagen
        slug = limpiar_slug(label)
        img_path = OUTPUT_DIR / f"{slug}.png"
        try:
            generar_imagen_scorecard(url.replace("www.", ""), label, promedio, scores, img_path)
        except Exception as e:
            log.warning(f"  Error generando imagen: {e}")
            continue

        # Generar texto
        titulo = random.choice(TITULOS).format(label=label, promedio=promedio)

        # Cuerpo
        hallazgos = data.get("hallazgos", [])
        hallazgos_html = ""
        for h in hallazgos[:5]:
            hallazgos_html += f"<li><strong>{h['categoria']}:</strong> {h['problema']}</li>\n"

        recomendaciones = data.get("recomendaciones", [])
        rec_html = ""
        for r in recomendaciones[:3]:
            rec_html += f"<li><strong>{r['titulo']}:</strong> {r['solucion']}</li>\n"

        promedio_color = "rojo" if promedio < 5 else ("amarillo" if promedio < 8 else "verde")
        table_rows = ""
        for cat, s in scores.items():
            color = "rojo" if s < 5 else ("amarillo" if s < 8 else "verde")
            table_rows += f"<tr><td>{cat}</td><td style='color:{color};font-weight:700'>{s}/10</td></tr>\n"

        cuerpo = f"""<p>Auditamos <strong>{label}</strong> con nuestro analizador automatico. Estos son los resultados reales:</p>

<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:16px 0'>
<h3 style='color:#58a6ff;margin:0 0 12px'>Scorecard — Promedio <span style='color:{promedio_color};font-size:24px'>{promedio}</span>/10</h3>
<table style='width:100%;border-collapse:collapse;color:#e6edf3'>
<tr><th style='text-align:left;padding:6px;border-bottom:1px solid #30363d'>Categoria</th><th style='text-align:left;padding:6px;border-bottom:1px solid #30363d'>Puntaje</th></tr>
{table_rows}
</table>
</div>

<h3>Problemas encontrados</h3>
<ul>{hallazgos_html}</ul>

<h3>Como arreglarlo</h3>
<ul>{rec_html}</ul>

<p>Incluso los sitios mas grandes tienen errores tecnicos que afectan su rendimiento, SEO y conversion.</p>

<p><a href='https://web-analyzer-1-l8uc.onrender.com/' style='display:inline-block;padding:14px 32px;background:#1f6feb;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;margin-top:12px'>Analiza tu sitio gratis →</a></p>

<p style='color:#8b949e;font-size:12px;margin-top:24px'>Analisis generado automaticamente por Web Analyzer. Resultados pueden variar segun el momento del dia y cambios en el sitio.</p>"""

        # Publicar
        log.info(f"  Publicando: {titulo[:70]}...")
        link = wp_publicar(titulo, cuerpo, slug, img_path, "auditorias")
        if link:
            marcar_sitio_usado(url)
            log.info(f"  OK: {link}")
            return True
        else:
            log.warning(f"  WP fallo la publicacion (intento {intento})")
            continue

    log.error(f"FALLO tras {MAX_REINTENTOS} intentos de auditoria.")
    return False


def generar_post_educativo():
    """Publica un post educativo de la lista. Retorna True si OK."""
    post = elegir_educativo()
    log.info(f"Post educativo: {post['titulo'][:70]}...")

    # Generar imagen
    img_path = OUTPUT_DIR / f"{post['slug']}.png"
    try:
        generar_imagen_educativa(post["titulo"], post["categoria"], img_path)
    except Exception as e:
        log.error(f"  Error generando imagen educativa: {e}")
        return False

    # Publicar
    link = wp_publicar(
        post["titulo"],
        post["cuerpo"],
        post["slug"],
        img_path,
        post["categoria"],
    )
    if link:
        marcar_educativo_usado(post["slug"])
        log.info(f"  OK: {link}")
    else:
        log.warning(f"  WP fallo la publicacion del educativo")
    return link is not None

def generar_imagen_vs(label1, prom1, label2, prom2, path):
    """Genera imagen comparativa VS para Facebook."""
    try:
        img = Image.new("RGB", (1200, 630), "#0d1117")
        draw = ImageDraw.Draw(img)
        try:
            font_title = ImageFont.truetype("C:/Windows/Fonts/Arialbd.ttf", 32)
            font_score = ImageFont.truetype("C:/Windows/Fonts/Arialbd.ttf", 72)
            font_label = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", 28)
            font_vs = ImageFont.truetype("C:/Windows/Fonts/Arialbd.ttf", 40)
        except Exception:
            font_title = ImageFont.load_default()
            font_score = font_title
            font_label = font_title
            font_vs = font_title
        bbox = draw.textbbox((0, 0), "VS", font=font_vs)
        vs_w = bbox[2] - bbox[0]
        draw.text(((1200 - vs_w) / 2, 30), "VS", fill="#f0883e", font=font_vs)
        color1 = "#1f6feb" if prom1 >= prom2 else "#8b949e"
        bbox = draw.textbbox((0, 0), label1, font=font_label)
        lw = bbox[2] - bbox[0]
        draw.text(((600 - lw) / 2, 100), label1, fill=color1, font=font_label)
        bbox = draw.textbbox((0, 0), f"{prom1}/10", font=font_score)
        sw = bbox[2] - bbox[0]
        draw.text(((600 - sw) / 2, 160), f"{prom1}/10", fill=color1, font=font_score)
        color2 = "#1f6feb" if prom2 >= prom1 else "#8b949e"
        bbox = draw.textbbox((0, 0), label2, font=font_label)
        lw = bbox[2] - bbox[0]
        draw.text((600 + (600 - lw) / 2, 100), label2, fill=color2, font=font_label)
        bbox = draw.textbbox((0, 0), f"{prom2}/10", font=font_score)
        sw = bbox[2] - bbox[0]
        draw.text((600 + (600 - sw) / 2, 160), f"{prom2}/10", fill=color2, font=font_score)
        draw.line([(600, 80), (600, 300)], fill="#30363d", width=2)
        try:
            font_footer = ImageFont.truetype("C:/Windows/Fonts/Arial.ttf", 20)
        except Exception:
            font_footer = font_label
        bbox = draw.textbbox((0, 0), "web-analyzer-1-l8uc.onrender.com", font=font_footer)
        fw = bbox[2] - bbox[0]
        draw.text(((1200 - fw) / 2, 560), "web-analyzer-1-l8uc.onrender.com", fill="#8b949e", font=font_footer)
        img.save(path, "PNG")
        log.info(f"  Imagen VS generada: {path}")
    except Exception as e:
        log.warning(f"  Error generando imagen VS: {e}")
        raise


def generar_post_vs():
    """Audita dos sitios competidores y publica un VS con comparativa."""
    tracking = cargar_tracking()
    usados_vs = tracking.get("vs", [])
    disponibles = []
    for (url1, label1), (url2, label2) in PARES_VS:
        key = f"{url1}|{url2}"
        if key not in usados_vs:
            disponibles.append(((url1, label1), (url2, label2), key))
    if not disponibles:
        log.info("Todos los VS fueron publicados. Reiniciando tracking VS.")
        tracking["vs"] = []
        guardar_tracking(tracking)
        for (url1, label1), (url2, label2) in PARES_VS:
            key = f"{url1}|{url2}"
            disponibles.append(((url1, label1), (url2, label2), key))
    (url1, label1), (url2, label2), key = random.choice(disponibles)
    log.info(f"VS: {label1} vs {label2}")
    try:
        resp1 = requests.post(ANALYZER_API, json={"url": url1, "depth": 1}, timeout=90)
        data1 = resp1.json()
        prom1 = data1.get("promedio", 0)
        scores1 = {}
        for cat, info in data1.get("scorecard", {}).items():
            scores1[cat] = info.get("puntaje", 0) if isinstance(info, dict) else info[0]
    except Exception as e:
        log.error(f"  Fallo auditoria {label1}: {e}")
        return False
    if not scores1 or prom1 == 0:
        log.warning(f"  Sin datos para {label1}")
        return False
    log.info(f"  {label1}: {prom1}/10")
    try:
        resp2 = requests.post(ANALYZER_API, json={"url": url2, "depth": 1}, timeout=90)
        data2 = resp2.json()
        prom2 = data2.get("promedio", 0)
        scores2 = {}
        for cat, info in data2.get("scorecard", {}).items():
            scores2[cat] = info.get("puntaje", 0) if isinstance(info, dict) else info[0]
    except Exception as e:
        log.error(f"  Fallo auditoria {label2}: {e}")
        return False
    if not scores2 or prom2 == 0:
        log.warning(f"  Sin datos para {label2}")
        return False
    log.info(f"  {label2}: {prom2}/10")
    if prom1 > prom2:
        ganador, perdedor = label1, label2
        prom_ganador, prom_perdedor = prom1, prom2
    elif prom2 > prom1:
        ganador, perdedor = label2, label1
        prom_ganador, prom_perdedor = prom2, prom1
    else:
        ganador, perdedor = None, None
        prom_ganador, prom_perdedor = prom1, prom2
    slug = limpiar_slug(f"{label1}-vs-{label2}")
    img_path = OUTPUT_DIR / f"{slug}.png"
    try:
        generar_imagen_vs(label1, prom1, label2, prom2, img_path)
    except Exception as e:
        log.warning(f"  Error generando imagen VS: {e}")
        img_path = None
    titulo = random.choice(TITULOS_VS).format(label1=label1, label2=label2)
    todas_cats = sorted(set(list(scores1.keys()) + list(scores2.keys())))
    table_rows = ""
    for cat in todas_cats:
        s1 = scores1.get(cat, 0)
        s2 = scores2.get(cat, 0)
        if s1 > s2:
            gana = f"<td style='text-align:center;padding:6px;color:#1f6feb'>{label1}</td>"
        elif s2 > s1:
            gana = f"<td style='text-align:center;padding:6px;color:#1f6feb'>{label2}</td>"
        else:
            gana = "<td style='text-align:center;padding:6px;color:#8b949e'>Empate</td>"
        table_rows += f"<tr><td style='padding:6px;border-bottom:1px solid #30363d'>{cat}</td><td style='text-align:center;padding:6px;border-bottom:1px solid #30363d'>{s1}/10</td><td style='text-align:center;padding:6px;border-bottom:1px solid #30363d'>{s2}/10</td>{gana}</tr>\n"
    color1 = "#1f6feb" if prom1 >= prom2 else "#8b949e"
    color2 = "#1f6feb" if prom2 >= prom1 else "#8b949e"
    hallazgos1 = data1.get("hallazgos", [])[:2]
    hallazgos2 = data2.get("hallazgos", [])[:2]
    h1_html = "".join(f"<li>{h['problema']}</li>" for h in hallazgos1)
    h2_html = "".join(f"<li>{h['problema']}</li>" for h in hallazgos2)
    if ganador:
        veredicto = f"<p><strong>Veredicto:</strong> El sitio de <strong style='color:#1f6feb'>{ganador}</strong> se lleva la victoria con {prom_ganador}/10 frente a {prom_perdedor}/10. Pero ambos tienen margen de mejora.</p>"
    else:
        veredicto = f"<p><strong>Empate tecnico</strong> en {prom1}/10. Dos sitios con fortalezas y debilidades distintas. +Cual te parece mejor a vos?</p>"
    cuerpo = f"""<p>Pusimos frente a frente a <strong>{label1}</strong> y <strong>{label2}</strong>. Ambos fueron auditados con la misma herramienta, en el mismo momento. Estos son los resultados:</p>
<div style='background:#161b22;border:1px solid #30363d;border-radius:8px;padding:20px;margin:16px 0'>
<h3 style='color:#58a6ff;margin:0 0 12px'>Cara a cara</h3>
<table style='width:100%;border-collapse:collapse;color:#e6edf3'>
<tr><th style='text-align:left;padding:8px;border-bottom:1px solid #30363d'>Categoria</th><th style='text-align:center;padding:8px;border-bottom:1px solid #30363d;color:{color1}'>{label1}</th><th style='text-align:center;padding:8px;border-bottom:1px solid #30363d;color:{color2}'>{label2}</th><th style='text-align:center;padding:8px;border-bottom:1px solid #30363d'>Gana</th></tr>
{table_rows}
<tr style='font-weight:700;font-size:16px;border-top:2px solid #30363d'><td style='padding:10px'>PROMEDIO</td><td style='text-align:center;padding:10px;color:{color1}'>{prom1}/10</td><td style='text-align:center;padding:10px;color:{color2}'>{prom2}/10</td><td style='text-align:center;padding:10px'>{"GANADOR" if ganador else "EMPATE"}</td></tr>
</table>
</div>
{veredicto}
<h3>Problemas en {label1}</h3>
<ul>{h1_html if h1_html else "<li>Ningun problema critico detectado</li>"}</ul>
<h3>Problemas en {label2}</h3>
<ul>{h2_html if h2_html else "<li>Ningun problema critico detectado</li>"}</ul>
<p><a href='https://web-analyzer-1-l8uc.onrender.com/' style='display:inline-block;padding:14px 32px;background:#1f6feb;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;margin-top:12px'>Audita tu sitio y compara con tu competencia --></a></p>
<p style='color:#58a6ff;font-weight:700;font-size:15px;margin-top:20px'>+Que opinas? +Quien deberia haber ganado? +Conoces un sitio que le gane a estos dos? Dejanos tu URL en los comentarios y lo auditamos.</p>
<p style='color:#8b949e;font-size:12px;margin-top:24px'>Analisis generado automaticamente por Web Analyzer. Resultados pueden variar segun el momento del dia y cambios en los sitios.</p>"""
    log.info(f"  Publicando VS: {titulo[:70]}...")
    link = wp_publicar(titulo, cuerpo, slug, img_path, "auditorias")
    if link:
        tracking = cargar_tracking()
        tracking.setdefault("vs", []).append(key)
        guardar_tracking(tracking)
        log.info(f"  OK: {link}")
        return True
    log.warning("  WP fallo la publicacion del VS")
    return False


# =============================================================================
# Scheduler
# =============================================================================

def main(tipo=None):
    """Publica 1 post. tipo=None rota entre auditoria, educativo y VS."""
    ahora = datetime.now()
    log.info(f"=== Web Analyzer — Generador de contenido === {ahora.isoformat()}")

    if tipo is None:
        tracking = cargar_tracking()
        n_auditorias = len(tracking.get("sitios", []))
        n_educativos = len(tracking.get("educativos", []))
        n_vs = len(tracking.get("vs", []))
        total = n_auditorias + n_educativos + n_vs
        # Rotacion: auditoria -> educativo -> vs -> auditoria...
        if total == 0:
            tipo = "auditoria"
        else:
            orden = total % 3
            if orden == 0:
                tipo = "auditoria"
            elif orden == 1:
                tipo = "educativo"
            else:
                tipo = "vs"

    if tipo == "educativo":
        log.info("Tipo: Post educativo")
        ok = generar_post_educativo()
    elif tipo == "vs":
        log.info("Tipo: VS")
        ok = generar_post_vs()
    else:
        log.info("Tipo: Auditoria")
        ok = generar_post_auditoria()

    log.info(f"=== Resultado: {'OK' if ok else 'FALLO'} ===\n")
    return ok


if __name__ == "__main__":
    ART = timezone(timedelta(hours=-3))

    def _ahora_art():
        return datetime.now(ART)

    def _ejecutar_si_corresponde():
        ahora = _ahora_art()
        if (ahora.hour == 8 or ahora.hour == 20) and ahora.minute < 5:
            log.info(f"[{ahora.strftime('%Y-%m-%d %H:%M:%S')}] Ejecutando publicacion programada...")
            main()

    log.info("=== Scheduler Web Analyzer iniciado ===")
    log.info("Publicara 1 articulo a las 08:00 y 20:00 ART (alternando auditoria/educativo)")
    log.info("Ejecucion inicial al arrancar...")
    main()

    while True:
        _ejecutar_si_corresponde()
        time.sleep(60)
