# WebAnalyzer & Optimizer — 200 casos de prueba adversariales (QA)

**Alcance auditado (código real):**
- Backend SaaS: `DelMonte/web-analyzer/app.py` (Flask), `analyzer.py` (motor de análisis),
  `database.py` (auth/usuarios), templates del render.
- Plugin generado: `webanalyzer_com_ar_optimizer.php` (2 versiones en los zips del workspace)
  y el generador `_generar_plugin_wordpress()` / `_generar_snippet_shopify()`.

**Convención por caso:** Input/escenario exacto → comportamiento esperado correcto →
severidad (crítico / alto / medio / bajo) → validación a agregar (si aplica).

> Los casos marcan **bugs reales encontrados en el código** (con referencia a la función)
> además de los escenarios de riesgo estándar. Donde dice «BUG REAL» el defecto existe hoy.

---

# A. Sitios atípicos / rotos (40 casos)

### A1. Sitio WordPress legítimo con Theme Divi + Elementor instalados a la vez
- **Input:** URL de un sitio con Divi y Elementor simultáneos (builder doble), H1 duplicados en shortcodes `[et_pb_text]` y `[elementor-template]`.
- **Esperado:** El análisis detecta la tecnología real (Divi + Elementor), no penaliza doble por shortcodes y el plugin generado respeta los builders (no reescribe el H1 renderizado).
- **Severidad:** Alto
- **Validación:** `_detectar_tecnologia()` debe buscar firmas en HTML renderizado, no en shortcodes crudos; el plugin debe excluir páginas con `et_fb=1` (frontend builder) del reescritor de H1.

### A2. Sitio con caché agresivo (LiteSpeed/W3TC/Cloudflare) que sirve HTML cacheado
- **Input:** `curl` al sitio devuelve `X-LiteSpeed-Cache: hit`; el HTML que ve el crawler es de hace 6 horas.
- **Esperado:** El análisis marca que la medición puede estar cacheada; el plugin (que usa `template_redirect` + `ob_start`) no debe asumir que sus cambios se aplicaron, y el reporte debe avisar «verificá con caché purgada».
- **Severidad:** Alto
- **Validación:** Comparar header `Age`/`X-Cache`/`CF-Cache-Status`; agregar `Cache-Control: no-cache` de advertencia en el reporte cuando hay caché activa.

### A3. Sitio con WAF/anti-bot (Cloudflare challenge, DataDome, Imperva)
- **Input:** URL pública detrás de un challenge JS que devuelve 403 con HTML de «Verificando que sos humano».
- **Esperado:** El análisis NO interpreta el HTML del challenge como el sitio real; devuelve error claro «el sitio está protegido por un WAF, no se pudo auditar» en vez de un scorecard basura de 2/10.
- **Severidad:** Crítico
- **Validación:** Detectar HTML típico de challenge (título «Just a moment…», script de challenge) y abortar con mensaje específico, no con `raise_for_status` genérico.

### A4. Sitio SPA renderizado solo en cliente (React/Vue sin SSR, sin prerender)
- **Input:** SPA pura: el HTML crudo tiene `<div id="root"></div>` vacío y todo se arma por JS.
- **Esperado:** El análisis detecta que no hay contenido renderizable y devuelve «sitio renderizado por JavaScript, se requiere headless browser»; NO genera scorecard de 1/10 por falta de H1/CTAs/meta (ver C16).
- **Severidad:** Crítico
- **Validación:** Si `len(html) < X` o `<div id="root">`/`<app>` sin contenido → flag «SPA detectado»; medir con Playwright/headless para estos casos o declarar auditoría limitada.

### A5. WordPress con versiones viejas: PHP 7.0 + WP 4.9
- **Input:** Sitio en PHP 7.0 (el plugin declara requisito PHP 7.4+).
- **Esperado:** El análisis detecta PHP/WP viejo y **no ofrece** el plugin WordPress (no es instalable); recomienda actualizar primero.
- **Severidad:** Alto
- **Validación:** Detectar versión vía `/wp-json/`, `generator` meta, headers `X-Powered-By`; bloquear descarga del plugin si PHP < 7.4 y avisar por qué.

### A6. Sitio multiidioma con WPML/Polylang (descripciones y metas por idioma)
- **Input:** Sitio es/en con `hreflang` y meta description distinta por idioma; el plugin borra TODAS las metas y pone una sola genérica (BUG REAL: regex en `_optimize_output` remueve todas las `<meta name=description>`).
- **Esperado:** El análisis respeta el multiidioma; el plugin NO debe eliminar metas por idioma ni inyectar una única description para todo el sitio.
- **Severidad:** Crítico
- **Validación:** No remover meta description existentes válidas; solo inyectar si no hay ninguna (y por locale).

### A7. WooCommerce con +5.000 productos (página pesada, catálogo gigante)
- **Input:** Tienda con 5.000+ productos; página de categoría de 3 MB de HTML.
- **Esperado:** El análisis termina en el timeout razonable sin OOM; no penaliza «Página pesada» con recomendación de lazy en el hero de producto; el plugin no crashea con regex sobre HTML gigante.
- **Severidad:** Medio
- **Validación:** Límite de tamaño de respuesta (p. ej. 5 MB) con truncado controlado; medir rendimiento por muestreo, no por página completa.

### A8. Sitio con login-wall (contenido solo para usuarios autenticados)
- **Input:** URL de un sitio cuyo contenido exige login; el crawler recibe solo la página de login.
- **Esperado:** El análisis detecta el patrón (formulario de login, no contenido) y lo informa; no puntúa una página de login como si fuera la home real.
- **Severidad:** Medio
- **Validación:** Detectar «login»/«password» en forms y ausencia de contenido → warning «página protegida».

### A9. Sitio con `robots.txt` que bloquea al crawler (`User-agent: * Disallow: /`)
- **Input:** `robots.txt` desautoriza la ruta; el crawler ignora robots y audita igual.
- **Esperado:** El análisis avisa «el sitio bloquea el rastreo» (ético/legal) y aun así entrega resultado con nota; el scorecard no debe penalizar SEO por páginas que el sitio decidió no indexar.
- **Severidad:** Medio
- **Validación:** Fetch de `robots.txt`; si bloquea, agregar aviso y bajar la confianza del score SEO.

### A10. Sitio con certificado TLS caducado o mixto (HTTP→HTTPS roto)
- **Input:** `https://sitio.com` con certificado vencido (error SSL) o que responde 403 en HTTPS y 200 en HTTP.
- **Esperado:** Error claro «certificado inválido»; el análisis no debe caer en un loop ni reportar «No se pudo conectar» sin explicación.
- **Severidad:** Medio
- **Validación:** `_safe_get` debe distinguir `SSLError` y exponer el motivo; fallback a HTTP solo con aviso.

### A11. Sitio que responde lentísimo (>15 s de TTFB) pero funcional
- **Input:** TTFB de 20 s (servidor con swap); el crawler tiene timeout de 15 s (BUG REAL: `_safe_get` timeout=15 sin retry).
- **Esperado:** El análisis reintenta al menos una vez antes de declarar error; el mensaje distingue «timeout» de «sitio caído».
- **Severidad:** Medio
- **Validación:** Retry con backoff (1 reintento); clasificar el error como «lento» y sugerir verificar hosting.

### A12. Sitio con redirección en cadena (5+ redirects) hasta www/no-www
- **Input:** URL con 6 redirects seguidos (http→https→www→trailing slash→param).
- **Esperado:** El análisis sigue hasta 10 hops (actual) pero avisa «muchos redirects» como hallazgo SEO; el scorecard usa la URL final para PSI y canonical.
- **Severidad:** Bajo
- **Validación:** Contar hops y reportar como hallazgo cuando > 3.

### A13. Sitio con redirect a otra zona horaria / país (geo-redirect)
- **Input:** `example.com` que redirige según IP del crawler (Googlebot vs otro UA) a versiones regionales distintas.
- **Esperado:** El análisis usa un UA fijo y avisa que el contenido puede variar por geolocalización; no debe presentar el contenido de una región como el del sitio completo.
- **Severidad:** Bajo
- **Validación:** Documentar UA usado en el reporte; opción de elegir país.

### A14. Sitio con HTML malformado (tags sin cerrar, entidades rotas)
- **Input:** HTML con `<div>` sin cerrar, `&amp` sin `;`, atributos sin comillas.
- **Esperado:** BeautifulSoup lo parsea tolerante; el análisis no crashea y los scores no se disparan por el parser.
- **Severidad:** Bajo
- **Validación:** Test de parser sobre corpus malformado; snapshots de regresión.

### A15. Sitio con `<h1>` dentro de `<svg>`/`<template>`/JS (falso conteo de H1)
- **Input:** Página con `<svg><text><h1>…` o `<template><h1>…` o un string JS `'<h1>'` en un script inline.
- **Esperado:** El conteo de H1 ignora SVG/template/scripts (el plugin v2 los reescribe con regex y puede romper JS — BUG REAL en `preg_replace_callback('/<h1[\s>]/i')`).
- **Severidad:** Crítico
- **Validación:** El plugin debe contar H1 solo fuera de `script/style/template/svg/noscript`; usar DOM, no regex global.

### A16. Sitio con imágenes `loading="eager"` explícito en el hero (LCP)
- **Input:** Hero con `loading="eager"` y `fetchpriority="high"` (WP 6.3+).
- **Esperado:** El análisis NO lo penaliza como «imagen sin lazy» (el hero NO debe ser lazy); el plugin respeta `eager` (BUG REAL: el lookahead `(?!.*loading=)` falla en tags multilínea y agrega `lazy`).
- **Severidad:** Alto
- **Validación:** Excluir LCP/hero de la recomendación de lazy; en el plugin, solo agregar `loading="lazy"` a `<img>` sin atributo `loading` DOM-real.

### A17. Sitio con imágenes en `<picture>`/`srcset` (formatos modernos)
- **Input:** `<picture><source srcset=".webp"><img src=".jpg">` con varias resoluciones.
- **Esperado:** El análisis reconoce WebP vía `source`; el plugin no duplica lazy ni rompe `srcset`.
- **Severidad:** Bajo
- **Validación:** `_formato_imagen` debe mirar `source` de `<picture>`, no solo `src`.

### A18. Sitio con `<noscript>` con imágenes de respaldo
- **Input:** `<noscript><img src="x.jpg"></noscript>` (fallback sin JS).
- **Esperado:** El plugin NO agrega `loading="lazy"` dentro de `<noscript>` (imagen de respaldo que nunca cargaría con JS desactivado — BUG REAL: regex `<img…>` sin exclusión de noscript).
- **Severidad:** Alto
- **Validación:** Excluir `<noscript>` del reescritor de imágenes.

### A19. Sitio que usa Cloudflare R2 / S3 / CDN para assets (URLs absolutas de otro dominio)
- **Input:** `<img src="https://cdn.otrodominio.com/x.webp">`.
- **Esperado:** `_extraer_imagenes` resuelve bien y el formato se detecta; el análisis no los marca como «externos» que penalizan (solo aplica a enlaces).
- **Severidad:** Bajo
- **Validación:** Distinguir CDN de assets vs enlaces externos de navegación.

### A20. Sitio con formulario de búsqueda (no newsletter) que tiene `type="email"`? — variante: login con campo email
- **Input:** Página de login con `<input type="email" name="email">` y botón «Ingresar».
- **Esperado:** NO se cuenta como «captura de email» de conversión (BUG REAL: `_extraer_forms.has_email` marca cualquier input email → infla Conversión).
- **Severidad:** Alto
- **Validación:** Detectar contexto del form (login/registro/búsqueda) por action/name/botón antes de sumar a conversión.

### A21. Sitio con formularios que cargan por AJAX/JS (aparecen después de 3 s)
- **Input:** Form de newsletter inyectado por JS (popup) — el HTML crudo no lo tiene.
- **Esperado:** El análisis avisa «no se detectaron forms en el HTML inicial (posible JS)»; no puntúa Conversión 4/10 por ausencia (ver A4/C16).
- **Severidad:** Alto
- **Validación:** Flag de render JS; si aplica, evaluar con headless.

### A22. Sitio que devuelve HTTP 200 con página de error «database connection lost»
- **Input:** Home responde 200 pero con «Error establishing a database connection» (WP roto).
- **Esperado:** El análisis detecta el patrón y lo reporta como error crítico del sitio (no un scorecard de SEO).
- **Severidad:** Alto
- **Validación:** Firmas de errores conocidas (DB error, 500 whitescreen, `fatal error` en HTML) → hallazgo crítico dedicado.

### A23. Sitio con charset ISO-8859-1 sin charset en headers (tildes rotas)
- **Input:** HTML en latin-1 sin `charset`, `resp.text` decodifica mal → tildes mojibake en title/description.
- **Esperado:** Los largos de title/description y el contenido se miden sobre la codificación correcta (detectar por `<meta charset>` del HTML antes que el default de requests).
- **Severidad:** Medio
- **Validación:** Usar `resp.encoding` derivado del HTML; validar longitud en caracteres Unicode reales.

### A24. Sitio con title de 200 caracteres y description de 5 (casos extremos de longitud)
- **Input:** `title` = 200 chars, `description` = 5 chars.
- **Esperado:** SEO baja 1 punto por title largo y 2 por description corta (actual); el reporte sugiere valores concretos (no genéricos).
- **Severidad:** Bajo
- **Validación:** Ninguna extra; cubrir en tests de umbrales de `_evaluar_seo`.

### A25. Sitio con 0 imágenes y 0 scripts (página texto puro)
- **Input:** Página minimalista solo texto, sin `<img>` ni `<script>`.
- **Esperado:** Rendimiento no se penaliza por «0 imágenes sin lazy» (división por `max(total,1)` ya cubierta); UX no inventa problemas.
- **Severidad:** Bajo
- **Validación:** Test de borde con página vacía de assets.

### A26. Sitio con iframes de terceros (YouTube, mapas, chat widgets)
- **Input:** Home con 5 iframes (video, mapa, widget de chat).
- **Esperado:** El análisis NO audita el contenido de los iframes como parte del sitio (no cuenta sus H1/forms/scripts como propios).
- **Severidad:** Medio
- **Validación:** Excluir `iframe`/`object`/`embed` de extracción de headings/forms/imágenes.

### A27. Sitio con menú off-canvas/modal cuyo contenido está en el HTML pero oculto (aria-hidden)
- **Input:** Modal y menú móvil con `aria-hidden="true"` conteniendo enlaces y un form.
- **Esperado:** El análisis no cuenta contenido oculto como CTA real ni como form de conversión visible.
- **Severidad:** Bajo
- **Validación:** Ignorar subárboles `aria-hidden`/`display:none`/`hidden` en `_extraer_forms` y `_extraer_enlaces`.

### A28. Sitio con 100+ imágenes (galería) — lista truncada a 20
- **Input:** Galería de 120 imágenes; `_extraer_imagenes` guarda `lista[:20]`.
- **Esperado:** Los totales (sin_alt, sin_lazy) se calculan sobre las 120 reales; la vista previa muestra 20 con aviso «mostrando 20 de 120».
- **Severidad:** Bajo
- **Validación:** Ninguna (ya correcto en totales); test con 120 imgs.

### A29. Sitio con lazy loading nativo correcto en el 100% de las imágenes
- **Input:** Todas las imágenes con `loading="lazy"` excepto hero con `eager`.
- **Esperado:** Rendimiento NO penaliza por lazy; recomendación de lazy no aparece (actual: `sin_lazy > 30%` gate — correcto).
- **Severidad:** Bajo
- **Validación:** Test de regresión de `_evaluar_rendimiento` con lazy completo.

### A30. Sitio con 4+ scripts bloqueantes (jQuery, plugins, analytics, chat)
- **Input:** 6 `<script src>` sin async/defer en head (chat, analytics, sliders).
- **Esperado:** Se reporta el hallazgo de scripts bloqueantes y la recomendación de defer; el plugin al aplicar defer NO debe romper los que dependen del orden (ver B25).
- **Severidad:** Medio
- **Validación:** Cruzar hallazgo A30 con caso B25 (defer que rompe).

### A31. Sitio con `meta robots noindex` en la página analizada
- **Input:** La URL analizada tiene `<meta name="robots" content="noindex,nofollow">`.
- **Esperado:** El análisis avisa «esta página no debe indexarse; el score SEO no aplica» (BUG REAL: `robots` se extrae pero nunca se evalúa).
- **Severidad:** Medio
- **Validación:** Si `noindex` → desactivar recomendaciones SEO para esa página y avisar.

### A32. Sitio con canonical apuntando a otra URL (www vs no-www, o paginación)
- **Input:** Canonical apunta a `https://www.sitio.com/page/2/` distinta de la URL analizada.
- **Esperado:** El análisis detecta canonical presente pero **no verifica coherencia** (BUG REAL: solo chequea existencia) → caso: canonical roto debe reportarse.
- **Severidad:** Medio
- **Validación:** Comparar canonical con URL final; hallazgo si difieren.

### A33. Sitio con og:image relativa (`/img/share.jpg`)
- **Input:** `og:image` = `/img/share.jpg` (relativa).
- **Esperado:** El análisis la resuelve a absoluta antes de reportar (BUG REAL: `_extraer_metadatos` no hace urljoin en og:image).
- **Severidad:** Bajo
- **Validación:** urljoin en og:image/twitter:image; validar que exista (HEAD).

### A34. Sitio que solo responde con AMP u otra variante al UA del crawler
- **Input:** UA tipo Chrome recibe AMP válida (distinta de la versión canónica).
- **Esperado:** El análisis avisa «se midió la variante AMP»; no confunde la puntuación de la versión normal.
- **Severidad:** Bajo
- **Validación:** Detectar `html[amp]`/`link rel=amphtml` y notarlo en el reporte.

### A35. Sitio con password en la URL (auth basic): `https://user:pass@host`
- **Input:** URL con credenciales embebidas.
- **Esperado:** El análisis no las guarda en logs/JSON ni las expone en el reporte (solo en el plan de la URL); BUG potencial: `_guardar_analisis` guarda `resultado["url"]` cruda.
- **Severidad:** Alto
- **Validación:** Sanear credenciales de la URL antes de loguear/persistir.

### A36. Sitio con URL que contiene query params gigantes o fragmentos raros
- **Input:** `https://sitio.com/?utm_source=x&utm_campaign=very-long&foo[]=bar` (incluye `[]` y `&`).
- **Esperado:** El análisis no crashea; PSI recibe la URL **URL-encodificada** (BUG REAL: `_fetch_pagespeed_insights` interpola `url` cruda en la query).
- **Severidad:** Medio
- **Validación:** `urlencode` el parámetro en la llamada a PSI; test con query especial.

### A37. Sitio con contenido 100% generado por usuario (foro) — texto de baja calidad
- **Input:** Foro con posts de usuarios; CTAs inexistentes; títulos generados.
- **Esperado:** El análisis NO recomienda «agregar newsletter» a un foro B2C activo (contexto); la recomendación debe ser contextual.
- **Severidad:** Bajo
- **Validación:** Heurística de tipo de sitio (foro/e-commerce/blog) antes de recomendar conversión.

### A38. Sitio con temática sensible (salud/legal/financiero) y formularios de contacto reales
- **Input:** Clínica con form de turnos (tiene datos personales de salud).
- **Esperado:** El análisis no expone en el reporte público contenido de esos forms; el plugin no agrega un newsletter duplicado sobre el form real (ver B12).
- **Severidad:** Alto
- **Validación:** No almacenar ni compartir valores de inputs; caso B12 para duplicados.

### A39. Sitio que usa `charset` en meta pero sirve UTF-16 (doble decodificación)
- **Input:** Respuesta UTF-16 con meta utf-8 → mojibake doble.
- **Esperado:** El análisis maneja la codificación detectada por header; los largos de título no se calculan sobre bytes.
- **Severidad:** Bajo
- **Validación:** Test de decodificación; usar `resp.apparent_encoding` como fallback.

### A40. Sitio con más de 10 redirects (loop de redirects)
- **Input:** Loop infinito de redirects (A→B→A→B…).
- **Esperado:** `_safe_get` corta a 10 hops y devuelve error claro «demasiados redirects» (no timeout genérico ni loop infinito).
- **Severidad:** Medio
- **Validación:** Detectar hop > 10 → `ValueError` específico; test de loop.

---

# B. Plugin auto-aplicado destructivo (50 casos)

### B1. Hosting sin extensión `mbstring` en PHP
- **Input:** Hosting compartido con PHP 7.4/8.0 sin mbstring; el plugin usa `mb_substr`/`mb_strlen` sin guardar (BUG REAL en `_build_meta_desc`/`_optimize_output`).
- **Esperado:** El plugin se desactiva solo con un aviso claro, no genera **white screen fatal** en todo el sitio.
- **Severidad:** Crítico
- **Validación:** `function_exists('mb_substr')` con fallback a `substr`, o check de extensión al activar con `register_activation_hook`.

### B2. Tema que no llama `wp_head()` ni `wp_footer()` (tema custom mal codificado)
- **Input:** Tema sin `wp_head()`: el plugin no inyecta meta; sin `wp_footer()`: no aparecen CTA ni newsletter ni trust bar.
- **Esperado:** El plugin no crashea; el cliente ve un aviso admin «tu tema no ejecuta wp_head/wp_footer, algunas correcciones no se aplican» en vez de creer que se aplicaron.
- **Severidad:** Alto
- **Validación:** Hook `admin_notices` que verifique `current_theme_supports`/presencia de hooks al activar.

### B3. Sitio con <img> multilínea (formateado por pretty-printer)
- **Input:** `<img\n  src="x.jpg"\n  class="y"\n  alt="foto">` (tags multilínea).
- **Esperado:** El reescritor de lazy (regex sin `s` flag) NO deja el tag partido a la mitad (BUG REAL: `<img(?!.*loading=)(.*?)>` corta en el primer `>` de la misma línea → HTML roto).
- **Severidad:** Crítico
- **Validación:** Reemplazar regex por parseo DOM (`DOMDocument::loadHTML` o `preg_replace` con `/s` + patrón correcto); test con tags multilínea.

### B4. `<img>` dentro de un string JS inline (`var tpl = '<img src="x">'`)
- **Input:** Script inline con plantilla `'<img src="thumb.jpg">'`.
- **Esperado:** El plugin NO altera contenido dentro de `<script>` (BUG REAL: regex de lazy y de H1 matchean dentro de scripts → rompe el JS del sitio).
- **Severidad:** Crítico
- **Validación:** Excluir `script/style/template/noscript/textarea` del reescritor (tokenizar el HTML, no regex global).

### B5. Sitio con más de un H1 y el segundo dentro de un bloque `display:none` o modal
- **Input:** Header con H1 + modal oculto con otro H1.
- **Esperado:** El plugin convierte solo H1 visibles redundantes y conserva el principal; no degrada estructura por H1 ocultos (regex v2 los cuenta).
- **Severidad:** Medio
- **Validación:** Contar H1 visibles (excluyendo `display:none`/`hidden`/`aria-hidden`).

### B6. Site con H1 generado por JS (React render en cliente)
- **Input:** El único H1 visible lo renderiza React después del parseo; el HTML crudo no tiene `<h1>`.
- **Esperado:** El plugin NO inyecta un H1 fantasma sobre un SPA que ya tiene H1 visual (BUG REAL: `_optimize_output` inyecta H1 oculto si no ve `<h1>` en HTML).
- **Severidad:** Alto
- **Validación:** No inyectar H1 si hay apps JS conocidas (`#root`, `data-reactroot`); o inyectar solo en páginas estáticas.

### B7. Sitio con title que contiene entidades (`Foo &amp; Bar`)
- **Input:** `<title>Foo &amp; Bar — Noticias</title>` de 65 caracteres reales.
- **Esperado:** El truncado no produce doble escape (BUG REAL: `strip_tags` + `esc_html` re-escaparía `&amp;` → el browser muestra «Foo &amp; Bar» en la pestaña).
- **Severidad:** Alto
- **Validación:** `html_entity_decode` antes de medir/truncar; volver a escapar una sola vez al emitir.

### B8. Sitio con descripción en inglés (multiidioma) y el plugin fuerza `og:locale = es_AR`
- **Input:** Sitio en inglés; plugin emite `og:locale es_AR` siempre (BUG REAL en `_og_tags`).
- **Esperado:** El locale se deriva del idioma del sitio (o se omite); no declara es_AR en un sitio en.
- **Severidad:** Medio
- **Validación:** Detectar `lang`/`hreflang` y usar `og:locale` acorde; test en/es/pt.

### B9. Sitio con producto WooCommerce: `the_content` del producto con shortcode de galería
- **Input:** `[gallery ids="1,2,3"]` en el contenido del producto; `_build_meta_desc` usa `wp_strip_all_tags` → la descripción cruda incluye el shortcode literal.
- **Esperado:** La meta description generada NO contiene `[gallery]` literal (BUG REAL: shortcodes sin expandir van al meta tag).
- **Severidad:** Medio
- **Validación:** `do_shortcode` + `wp_strip_all_tags` antes de generar la descripción; o usar excerpt prioritario.

### B10. Sitio con excerpt de 500 caracteres que contiene HTML y emojis
- **Input:** Excerpt largo con `<p>` y emojis; truncado por `mb_substr(…, 155)`.
- **Esperado:** El truncado no corta un emoji por la mitad (secuencia surrogate) ni deja HTML abierto.
- **Severidad:** Bajo
- **Validación:** Truncado por code points (mb) y `force_balance_tags`/`wp_trim_words`.

### B11. El cliente ya tiene Yoast/RankMath activos (SEO plugin instalado)
- **Input:** Sitio con Yoast; el plugin elimina las meta description de Yoast (regex en `_optimize_output`) e inyecta la propia genérica.
- **Esperado:** El plugin detecta otro SEO plugin y NO pisa sus metas (conflicto directo — BUG REAL).
- **Severidad:** Crítico
- **Validación:** `is_plugin_active('wordpress-seo/wp-seo.php')` o `rank-math/rank-math.php` → desactivar el reescritor de metas y avisar.

### B12. Sitio que YA tiene newsletter propio (el análisis lo detectó)
- **Input:** El análisis marca «con_email: 1» pero el plugin igual agrega un segundo newsletter + CTA flotante.
- **Esperado:** Si el sitio ya captura email, el plugin NO duplica el newsletter ni el CTA flotante (duplicación directa — BUG REAL: el generador agrega `[newsletter]` y CTA siempre).
- **Severidad:** Alto
- **Validación:** Parametrizar el plugin por hallazgos reales: solo agregar newsletter si `con_email == 0`.

### B13. El CTA flotante tapa el botón «Comprar» del propio sitio en mobile
- **Input:** Sitio e-commerce mobile con botón de compra flotante propio en bottom-right; el CTA del plugin se superpone (z-index 9999).
- **Esperado:** El CTA no tapa CTAs existentes del sitio (canibalización de conversión).
- **Severidad:** Alto
- **Validación:** No inyectar CTA flotante si ya hay botones flotantes/sticky (detectar `position:fixed`); o hacerlo configurable.

### B14. Sitio con barra admin de WordPress visible (usuario logueado) + CTA flotante
- **Input:** El admin navega el sitio logueado; el CTA flotante y la trust bar aparecen también para el admin.
- **Esperado:** Las correcciones de conversión no se muestran a usuarios logueados/admin (no afectan al dueño del sitio).
- **Severidad:** Medio
- **Validación:** Excluir `is_user_logged_in()`/`current_user_can` de CTAs y trust bar.

### B15. Ancla `#newsletter` sin destino (el shortcode falló por tema sin wp_footer)
- **Input:** CTA `href="#newsletter"` pero no existe ningún elemento con id newsletter en la página.
- **Esperado:** No se genera un enlace muerto; si no hay newsletter, el CTA no se emite.
- **Severidad:** Bajo
- **Validación:** Solo emitir CTA si el shortcode de newsletter estará presente.

### B16. Sitio con caching de página (LiteSpeed) + plugin con ob_start en `template_redirect`
- **Input:** Página cacheada: el buffer corre o no según el orden de hooks del caché; resultados inconsistentes entre visits.
- **Esperado:** El plugin funciona con cachés populares (purga al activar/desactivar; `LiteSpeed_Cache_API::purge_all()`), sin servir HTML a medias.
- **Severidad:** Alto
- **Validación:** Registrar purga de caché en activación; probar con W3TC/LiteSpeed/Super Cache.

### B17. Otro plugin usa `ob_start` con callback (conflicto de buffers anidados)
- **Input:** Plugin de optimización existente también hace output buffering; el orden de `ob_end_flush` mezcla los callbacks.
- **Esperado:** Los buffers anidados se respetan; el HTML final no queda duplicado ni truncado.
- **Severidad:** Alto
- **Validación:** Prioridad de `template_redirect` alta (99) y flush controlado; test con 2 buffers.

### B18. WooCommerce: el buffer captura la página de producto y el lazy rompe el slider de imágenes
- **Input:** Slider de producto (flexslider/owl) con imágenes; agregar `loading="lazy"` a las del slider rompe la navegación del carrusel.
- **Esperado:** Las imágenes dentro de sliders conocidos se excluyen del lazy forzado.
- **Severidad:** Alto
- **Validación:** Detectar contenedores `.flexslider`, `.owl-carousel`, `.slick`, `[data-slider]` y no forzar lazy.

### B19. Sitio con `defer` en script que otro inline usa vía `document.write`
- **Input:** Inline script que hace `document.write('<script src="lib.js">')` y luego usa esa lib; el plugin agrega `defer` a lib.js.
- **Esperado:** El defer no rompe la secuencia de carga (document.write + defer = página vaciada en algunos browsers).
- **Severidad:** Crítico
- **Validación:** No aplicar defer a scripts cargados por `document.write`; detectar `document.write` en inline scripts y desactivar defer global.

### B20. Script enqueue con `jquery` en el handle pero que NO es jQuery (ej. `jquery-lightbox` usa `jquery` core, ok; pero `jquery.foo` handle)
- **Input:** Handle `jquery-foo` (plugin mal enqueueado) — `strpos($handle,'jquery') === 0` lo exime aunque no sea jQuery.
- **Esperado:** El fallo es conservador (no defer a nada con «jquery») — aceptable; documentar que puede dejar scripts bloqueantes sin optimizar.
- **Severidad:** Bajo
- **Validación:** Whitelist explícita de handles jQuery reales (`jquery`, `jquery-core`, `jquery-migrate`, `jquery-ui-*`).

### B21. Script enqueueado por core de WP 6.3+ con `defer` ya presente (WP agrega defer a algunos)
- **Input:** `$tag` ya contiene `defer`; `str_replace(' src=', ' defer src=')` agrega un segundo `defer` → `defer defer` (inofensivo pero sucio).
- **Esperado:** No duplicar atributos; solo agregar si no existe.
- **Severidad:** Bajo
- **Validación:** Comprobar `strpos($tag, 'defer') === false` antes de insertar.

### B22. Sitio con `async` en el script (Google Analytics)
- **Input:** `<script async src="...analytics.js">` → `str_replace` produce `async defer` (async gana — sin cambio real).
- **Esperado:** Sin regresión; documentar que async no se toca.
- **Severidad:** Bajo
- **Validación:** Test unitario del filtro con async+defer.

### B23. Sitio que depende de scripts en orden estricto (script B usa global definida por A)
- **Input:** A define `window.helper`, B la usa; ambos sin async; plugin pone defer a ambos → B puede ejecutarse antes que A (orden de defer no garantizado).
- **Esperado:** El plugin NO agrega defer indiscriminadamente a scripts enlazados por dependencias (solo a los seguros), o preserva el orden (defer mantiene orden de aparición EN EL MISMO documento — el riesgo es con dependencias entre defer y inline).
- **Severidad:** Alto
- **Validación:** Análisis de dependencias (registros `wp_script_add_data`) o modo conservador: solo defer a scripts de analytics/chat/third-party con `async` ya.

### B24. Inline script que usa `$(document).ready` con jQuery en footer cargado de forma diferida por el propio tema
- **Input:** jQuery en footer sin `wp_enqueue` ordenado; el plugin exime por handle «jquery» pero el orden real del tema rompe todo.
- **Esperado:** El plugin no empeora el estado; el test debe confirmar que no introduce regresión sobre un sitio ya frágil.
- **Severidad:** Medio
- **Validación:** Test en sitio de referencia frágil (fixture) comparando antes/después del plugin.

### B25. Plugins de chat/CRM (Tawk.to, Crisp, HubSpot) cuyo script usa `defer`+`document.write`
- **Input:** Widget de chat con `document.write`; al agregar defer el widget desaparece o rompe el layout.
- **Esperado:** Los widgets de terceros conocidos se excluyen del defer.
- **Severidad:** Crítico
- **Validación:** Lista de handles/URLs de terceros a excluir (tawk, crisp, hubspot, intercom, zendesk).

### B26. El plugin se instala en un sitio con `define('WP_DEBUG', true)` y warnings de deprecación PHP 8.1
- **Input:** PHP 8.1 con deprecation notices de funciones `strftime`/dinámicas; el buffer captura notices y los inyecta en el HTML.
- **Esperado:** El plugin no emite notices (código compatible PHP 8.x) ni corrompe el buffer con warnings.
- **Severidad:** Medio
- **Validación:** Correr el plugin con `E_ALL` en PHP 8.0/8.1/8.2 y cero warnings.

### B27. Sitio con `load more`/paginación infinita por AJAX
- **Input:** El contenido de la página cargado por AJAX al scrollear; los cambios del plugin (lazy, alt) no se aplican a ese contenido dinámico.
- **Esperado:** Los `loading="lazy"` no rompen la paginación AJAX (las imágenes nuevas ya son lazy por el browser nativo).
- **Severidad:** Bajo
- **Validación:** Test con fixture de infinite scroll; verificar que el reescritor no toca respuestas AJAX.

### B28. Sitio con formulario de suscripción que envía a un servicio externo (Mailchimp) — el plugin agrega el suyo
- **Input:** El sitio ya integra Mailchimp; el plugin agrega `[newsletter]` con `<form action="">` que **no procesa nada** (BUG REAL: el form del plugin no tiene handler → los emails se pierden).
- **Esperado:** El plugin no agrega un form muerto; si agrega newsletter, debe procesarlo (guardar en DB/opción) o conectar con un servicio.
- **Severidad:** Crítico
- **Validación:** No emitir el form sin handler real; o implementar handler con nonce + almacenamiento.

### B29. El form del newsletter recibe envíos masivos (spam)
- **Input:** Bots completan el form del plugin (`action=""`, sin nonce, sin honeypot, sin captcha) → miles de posts al mismo URL.
- **Esperado:** El form no permite spam (nonce + honeypot + rate limit); los emails no se pierden ni se guardan basura.
- **Severidad:** Alto
- **Validación:** `wp_nonce_field`, campo honeypot oculto, `sanitize_email` y guardar con `wp_insert_post` o transient.

### B30. Cliente instala el plugin en un Multisite (red WP)
- **Input:** Multisite; el plugin se activa en red; los hooks corren por sitio; los prefijos de funciones son por dominio analizado.
- **Esperado:** El plugin funciona en Multisite sin colisión de funciones entre sitios de la red (nombres únicos por `safe_domain` — ya, pero el folder del plugin es único).
- **Severidad:** Medio
- **Validación:** Test en multisite; documentar limitación (un solo sitio analizado por instalación).

### B31. El cliente analiza el sitio y descarga el plugin, luego cambia de dominio (migración)
- **Input:** El plugin tiene el dominio viejo hardcodeado en `Plugin URI`, instrucciones y nombre de carpeta.
- **Esperado:** Los textos no rompen nada tras migrar (no afectan función); documentar que debe regenerarse.
- **Severidad:** Bajo
- **Validación:** Ninguna crítica; nota en el README del plugin.

### B32. El plugin se activa y el sitio tiene 500 por un fatal en `preg_replace` (patrón inválido por comilla en el site_name)
- **Input:** `safe_domain` está sanitizado, pero `site_name`/`site_desc`/`site_url` se interpolan **sin escapar** en el código PHP generado (BUG REAL en `_generar_plugin_wordpress` — ver E30): si el sitio analizado tiene un title con `'`, el PHP generado puede tener comillas rotas → fatal al instalar.
- **Esperado:** El PHP generado es siempre sintácticamente válido (escapar comillas/PHP en todas las interpolaciones).
- **Severidad:** Crítico
- **Validación:** Escapar `'`/`\`/`*/` en site_name/site_desc/site_url antes de interpolar; test con títulos maliciosos (ver E30-E32).

### B33. Instalar el plugin de DOS análisis distintos (dos dominios) → dos plugins con funciones distintas
- **Input:** Instalar plugin de `sitioA.com` y de `sitioB.com`; los prefijos de funciones difieren (`sitio_a_…`, `sitio_b_…`) → coexisten.
- **Esperado:** Coexistencia sin colisión (ya por diseño con safe_domain) — test de confirmación.
- **Severidad:** Bajo
- **Validación:** Test de instalación dual.

### B34. El plugin no tiene página de configuración ni «modo seguro»/rollback
- **Input:** El cliente quiere aplicar solo SEO, no el CTA flotante; no hay opción.
- **Esperado:** El plugin aplica todo o nada (actual) → caso de diseño: al menos un filtro `apply_filters('webanalyzer_fixes', $fixes)` y una página de opciones con checkboxes.
- **Severidad:** Medio
- **Validación:** Implementar opciones (register_setting) con cada fix como toggle.

### B35. Desinstalación: `uninstall.php` inexistente y opciones temporales sin limpiar
- **Input:** Se desactiva/borra el plugin; los hooks se quitan solos (desactivación), pero no hay limpieza de opciones/transients.
- **Esperado:** Borrar el plugin deja el sitio exactamente como estaba (sin opciones huérfanas ni cambios residuales).
- **Severidad:** Bajo
- **Validación:** `uninstall.php` con `delete_option` de lo que se persista.

### B36. El plugin corre su buffer en páginas de búsqueda/archivo/categoría (archives)
- **Input:** Archive de categoría: meta description = la del blog (genérica) para todas las páginas de archivo → **duplicación masiva de meta descriptions** en todo el sitio.
- **Esperado:** No generar la misma description genérica en todas las páginas (SEO negativo neto — BUG REAL: `_build_meta_desc` usa `get_bloginfo('description')` para todo lo que no es single/page).
- **Severidad:** Alto
- **Validación:** En archives usar la descripción del término/categoría, o no inyectar si es genérica.

### B37. Página 404 (página no encontrada) — el plugin inyecta meta description igual
- **Input:** URL 404 dentro del sitio; WordPress sirve la página 404; el plugin le agrega meta description y H1 oculto.
- **Esperado:** No optimizar páginas 404 (pueden tener `noindex` por defecto); no agregar contenido a una página de error.
- **Severidad:** Bajo
- **Validación:** `is_404()` → saltar reescritura.

### B38. Feed RSS — el buffer corre sobre feeds
- **Input:** `template_redirect` no dispara en feeds (correcto) — verificar que el plugin NO altera `?feed=rss2`.
- **Esperado:** Feeds intactos (sin meta tags ni H1 inyectados).
- **Severidad:** Bajo
- **Validación:** Test con `/feed/`.

### B39. El plugin y un theme builder (Elementor) con `elementor-pro` que hace SSR propio
- **Input:** Elementor renderiza en servidor partes del HTML; el reescritor de H1 de v2 puede convertir el H1 del template de Elementor a H2 y romper estilos del builder.
- **Esperado:** No modificar H1 en markup de builders (clases `elementor-*`, `et_pb_*`).
- **Severidad:** Alto
- **Validación:** Excluir de la reescritura nodos con clases de builders conocidos.

### B40. El plugin se sube a un hosting con `register_argc_argv`/restricciones de funciones deshabilitadas
- **Input:** Hosting bloquea `preg_replace` con `/e` (obsoleto) — no se usa; pero bloquea `ob_start` con callback en algunos hosts → fatal.
- **Esperado:** Fallback si `ob_start` con callback no está disponible; aviso admin en vez de white screen.
- **Severidad:** Alto
- **Validación:** Try/catch alrededor de `ob_start`; si falla, notice y continuar sin buffer.

### B41. Sitio con `Content-Security-Policy` estricta que bloquea inline styles del plugin
- **Input:** CSP sin `unsafe-inline`; los `style="…"` inline del CTA/newsletter/trust bar se bloquean → elementos sin estilo o no visibles.
- **Esperado:** El plugin degrada con gracia (los elementos se ven, aunque sin estilo perfecto) y no rompe la página.
- **Severidad:** Medio
- **Validación:** Avisar si la página tiene CSP que bloquee inline; minimizar inline styles.

### B42. Sitio con AMP cacheado (Google AMP Cache) — el plugin corre sobre la versión AMP
- **Input:** La página AMP se sirve desde el cache de Google; los cambios del plugin no se ven hasta revalidar.
- **Esperado:** El plugin no interfiere con AMP (los hooks de AMP desactivan plugins no-AMP en `amp_skip_*`).
- **Severidad:** Bajo
- **Validación:** Verificar compatibilidad con el plugin oficial AMP.

### B43. Sitio con lazy loading ya nativo en navegadores y el plugin agrega `loading="lazy"` también al hero
- **Input:** Hero sin atributo loading; el plugin lo hace lazy → **LCP empeora** (imagen crítica diferida) — el «fix» daña el CWV que pretendía mejorar.
- **Esperado:** El plugin NO aplica lazy a la primera imagen visible (LCP); aplicar solo below-the-fold.
- **Severidad:** Crítico
- **Validación:** Detectar LCP (primera imagen grande en viewport / `fetchpriority`) y excluirla.

### B44. Sitio con imágenes sin `width`/`height` → CLS al agregar lazy
- **Input:** Imágenes sin dimensiones; al diferirlas, el layout «salta» cuando cargan → **CLS sube**.
- **Esperado:** El plugin reserva el espacio (añade `width`/`height` si faltan, o avisa) para no empeorar CLS.
- **Severidad:** Alto
- **Validación:** Para imgs sin dimensiones: extraer del `srcset`/dimensiones reales o no aplicar lazy.

### B45. Sitio con `preload`/`preconnect` para el hero (WP core) — el plugin no los toca
- **Input:** `<link rel="preload" as="image" href="hero.jpg">` — verificar que el reescritor no rompe el preload al cambiar el src de la img.
- **Esperado:** Preloads intactos y coherentes con los src finales.
- **Severidad:** Bajo
- **Validación:** Test de no-regresión con preloads.

### B46. Sitio con datos de usuario en `post_content` privados (páginas draft)
- **Input:** El plugin usa `$post->post_content` sin filtrar por `post_status`/`post_type` válidos; drafts con contenido confidencial podrían aparecer si el excerpt falla (bajo riesgo real, pero el contenido se expone al meta).
- **Esperado:** Solo contenido público publicado se usa para metas.
- **Severidad:** Medio
- **Validación:** `is_post_publicly_viewable()` antes de usar el contenido.

### B47. El `esc_attr` de la meta description con comillas dobles de la descripción
- **Input:** Descripción con `"` y `'`; `esc_attr` las escapa correctamente (ok) — test de regresión con caracteres especiales `" ' < > &`.
- **Esperado:** Meta válida sin romper el HTML (esc_attr ya cubre).
- **Severidad:** Bajo
- **Validación:** Test unitario de escaping.

### B48. Título del sitio con `</title>` dentro (inyección de tag en el nombre del sitio)
- **Input:** `get_bloginfo('name')` con `</title><script>` (nombre de sitio malicioso) → inyección en `<title>`.
- **Esperado:** `esc_html` protege el título emitido (ok en runtime) — test de regresión.
- **Severidad:** Bajo
- **Validación:** Test de escaping en título/H1/og:title.

### B49. El plugin genera `og:image` con la PRIMERA imagen del contenido de la home (fallback v2)
- **Input:** La primera imagen del contenido es un tracking pixel de 1x1 o un banner — el fallback la usa como og:image → **tarjetas de redes sociales rotas** (BUG REAL en el fallback `preg_match('/<img[^>]+src=…/')`).
- **Esperado:** El fallback elige una imagen significativa (no pixel/banner/logo duplicado) o no emite og:image.
- **Severidad:** Alto
- **Validación:** Filtrar por tamaño (descartar < 200px), `data:` URIs y archivos de tracking.

### B50. El plugin se instala en un sitio con `WP_ROCKET`/otro optimizador que ya hace lazy y defer
- **Input:** WP Rocket activo (ya lazy/defer); el plugin duplica atributos y reescribe HTML que WP Rocket ya procesó → conflictos de render.
- **Esperado:** Detectar optimizadores conocidos (WP Rocket, Autoptimize, LiteSpeed) y desactivar los fixes redundantes (lazy/defer) para evitar doble procesamiento.
- **Severidad:** Alto
- **Validación:** `is_plugin_active` de optimizadores → solo aplicar fixes de SEO/UX que no dupliquen.

---

# C. Falsos positivos / negativos en el análisis (40 casos)

### C1. Sitio B2B corporativo sin newsletter (no lo necesita)
- **Input:** Sitio corporativo de servicios con form de contacto y teléfono, sin newsletter.
- **Esperado:** NO recomendar «agregá un newsletter» (BUG REAL: `_generar_recomendaciones` lo sugiere siempre que `con_email == 0`).
- **Severidad:** Alto
- **Validación:** Contextualizar por tipo de sitio (contacto = conversión válida); solo recomendar newsletter si hay contenido editorial (blog/noticias).

### C2. Sitio con descripción de 200 caracteres perfectamente válida (Google muestra ~160)
- **Input:** Meta description de 190 chars; el evaluador la penaliza (-1).
- **Esperado:** Penalización leve con nota «se truncará en SERP» es aceptable — pero no debe tratarse como hallazgo crítico.
- **Severidad:** Bajo
- **Validación:** Umbral de hallazgo en ≥ 2 puntos, no en 1.

### C3. Sitio con título de 25 caracteres corto pero de marca (ej. «Banco X»)
- **Input:** Title «Banco Rivadavia» (15 chars) — corto pero intencional.
- **Esperado:** El aviso «title muy corto» existe (correcto), pero no debe recomendar rellenar con relleno artificial; sugerencia contextual.
- **Severidad:** Bajo
- **Validación:** Ninguna crítica; revisar redacción de la recomendación.

### C4. Sitio con JSON-LD (schema.org) en vez de meta description
- **Input:** Descripción vía `itemprop="description"` o JSON-LD `@graph[description]`, sin `<meta name="description">`.
- **Esperado:** El análisis reconoce JSON-LD como descripción válida (BUG REAL: `_extraer_metadatos` solo mira `meta[name=description]` → falso «falta descripción» en sitios modernos).
- **Severidad:** Alto
- **Validación:** Extraer `description` de JSON-LD y `itemprop`; usarlos como fallback.

### C5. Sitio con og:image de 600×315 válida (mínimo real de Facebook)
- **Input:** og:image 600×315; el análisis solo verifica existencia (no tamaño) — aceptable; pero el plugin lo usa sin verificar que la URL siga viva.
- **Esperado:** Verificar HTTP 200 de og:image (imagen rota → hallazgo real).
- **Severidad:** Bajo
- **Validación:** HEAD request a og:image; si 404 → hallazgo «og:image rota».

### C6. Sitio con H1 correcto y H2 correctos pero con widgets H3 en footer (jerarquía «rota»)
- **Input:** h1 → h2 → (widgets) h3; `_verificar_jerarquia` ve h1,h2,h3 → ok. Variante: h1 → h3 (sin h2) en una página de aterrizaje.
- **Esperado:** La página de aterrizaje con h1→h3 se marca «jerarquía rota» — correcto semánticamente, pero el mensaje debe ser claro para el cliente.
- **Severidad:** Bajo
- **Validación:** Mensaje con ejemplo concreto (textos de los headings).

### C7. Sitio con 3 H1 por diseño de landing (sections independientes)
- **Input:** Landing moderna con H1 por sección (patrón cuestionable pero común).
- **Esperado:** Penalización leve (-1) y recomendación de unificar — correcto; no tratarlo como fallo crítico.
- **Severidad:** Bajo
- **Validación:** Gravedad «alta» solo si además faltan H2/H3.

### C8. Sitio con imágenes decorativas con `alt=""` (correcto según WCAG)
- **Input:** Íconos decorativos con `alt=""` (alt vacío es VÁLIDO en accesibilidad).
- **Esperado:** El análisis NO los cuenta como «imágenes sin alt» (BUG REAL: `sin_alt` cuenta `not i["alt"]` incluyendo `alt=""` decorativo).
- **Severidad:** Alto
- **Validación:** `alt=""` → decorativo → no penalizar; solo penalizar imágenes sin atributo alt (o con alt de texto de relleno).

### C9. Sitio con imágenes cuyo alt es genérico («imagen», «foto», «image»)
- **Input:** 30 imágenes con `alt="imagen"` repetido.
- **Esperado:** El análisis detecta alt genéricos como problema real (actualmente no los distingue).
- **Severidad:** Medio
- **Validación:** Lista negra de alts genéricos (imagen/foto/image/photo/untitled) → contar como «sin alt útil».

### C10. Sitio con skip-link en inglés («Skip to content») — detección correcta
- **Input:** `Skip to content` (en) — regex `saltar|skip` con `re.I` lo detecta — ok.
- **Esperado:** Sin penalización (ya no penaliza); test de regresión para no reactivar el `score -= 0` muerto.
- **Severidad:** Bajo
- **Validación:** Limpiar el código muerto de skip-link y testear.

### C11. Sitio con formulario sin `<label>` pero con `aria-label` en cada input
- **Input:** Form con `aria-label="Email"` en inputs, sin tags `<label>`.
- **Esperado:** NO penalizar «formulario sin labels» (BUG REAL: `_evaluar_accesibilidad` solo mira `<label>`, ignora `aria-label`/`aria-labelledby`/`title`).
- **Severidad:** Alto
- **Validación:** Contar inputs con `aria-label`/`aria-labelledby`/`title` como accesibles.

### C12. Sitio con placeholder como único indicador de campo (mala práctica pero común)
- **Input:** Form con `placeholder="Email"` sin label ni aria-label.
- **Esperado:** Penalizar (correcto) — el placeholder no es label; mensaje educativo.
- **Severidad:** Bajo
- **Validación:** Mantener penalización; redactar bien el hallazgo.

### C13. Sitio con contraste de colores bajo pero el análisis NO lo mide
- **Input:** Texto gris #999 sobre blanco (contraste 2.8:1) — falla WCAG AA.
- **Esperado:** El análisis no mide contraste (no está implementado) → **falso negativo crítico** en Accesibilidad: el score dice 9/10 con contraste roto.
- **Severidad:** Crítico
- **Validación:** Implementar chequeo de contraste (al menos para colores de texto/fondo en CSS inline y estilos comunes).

### C14. Sitio con menú no operable por teclado (sin foco visible)
- **Input:** Menú hover-only sin `:focus`; no se puede navegar con Tab.
- **Esperado:** El análisis no detecta foco/teclado (no implementado) → falso negativo en Accesibilidad.
- **Severidad:** Alto
- **Validación:** Aviso «auditoría de accesibilidad limitada a lo estático; verificar teclado/foco manualmente» en el reporte.

### C15. Sitio con HTML válido pero sin `lang` en `<html>`
- **Input:** `<html>` sin atributo lang (WCAG 3.1.1).
- **Esperado:** Detectar y penalizar levemente (no implementado → falso negativo).
- **Severidad:** Medio
- **Validación:** Agregar chequeo `html[lang]`.

### C16. SPA con todo el contenido renderizado por JS — auditoría «vacía»
- **Input:** SPA CSR (ver A4): sin meta, sin H1, sin forms en HTML crudo.
- **Esperado:** El scorecard no debe decir SEO 1/10 / UX 3/10 sobre una página que en el navegador está perfecta (falso negativo masivo — BUG REAL: `analizar()` usa solo HTML crudo).
- **Severidad:** Crítico
- **Validación:** Detección SPA + medición con headless o advertencia explícita.

### C17. Sitio con caché de página que sirve HTML «bien» al crawler pero roto al usuario
- **Input:** Caché sirve una versión completa correcta; el sitio real está roto para usuarios (caso inverso de A2).
- **Esperado:** Reportar que la medición puede no reflejar el estado real con caché activa.
- **Severidad:** Bajo
- **Validación:** Nota de caché en el reporte (ver A2).

### C18. Dos análisis del mismo sitio en 10 minutos dan scores distintos (no-determinismo)
- **Input:** `analyze` del mismo URL dos veces; PSI caído en la primera (fallback heurístico) y OK en la segunda → score salta de 5 a 8.
- **Esperado:** Los scores son estables entre corridas; cuando PSI falla, el reporte marca «medición parcial» en lugar de cambiar silenciosamente el score.
- **Severidad:** Alto
- **Validación:** Marcar en el scorecard cuándo se usó solo heurística (sin PSI); no mezclar.

### C19. Sitio lento de verdad (PSI bajo) pero HTML liviano (heurística alta)
- **Input:** HTML 50 KB con 1 imagen, pero LCP 12 s (JS pesado, backend lento) → heurística 9/10, PSI 3/10 → blend 6.6.
- **Esperado:** El blend 60/40 reduce el error (ya implementado) — pero el detalle debe explicar la discrepancia «HTML liviano pero LCP alto: el cuello de botella es el backend/JS».
- **Severidad:** Medio
- **Validación:** Reportar la discrepancia heurística vs PSI como hallazgo propio.

### C20. Sitio con CSS externo enorme (no contado en size_kb)
- **Input:** HTML 80 KB + CSS 400 KB + JS 600 KB; `size_kb` solo mide el HTML (BUG REAL) → «página liviana» cuando pesa 1 MB.
- **Esperado:** Estimar el peso total (sumando CSS/JS referenciados) o aclarar que se mide solo HTML.
- **Severidad:** Medio
- **Validación:** Fetch HEAD de CSS/JS principales y sumar; o renombrar el hallazgo «HTML de X KB».

### C21. Sitio con 1 sola imagen PNG de logo (formato correcto para logo)
- **Input:** Solo el logo PNG (transparencia); «PNG sin WebP» penaliza -2 — falso positivo (un logo PNG con transparencia no necesita WebP).
- **Esperado:** No penalizar si el PNG es el logo/pequeño o si hay razones de transparencia; penalizar catálogos de fotos JPEG/PNG.
- **Severidad:** Medio
- **Validación:** Excluir logos (dimensiones pequeñas) y penalizar solo fotos grandes.

### C22. Sitio con imágenes `.gif` animadas (los formatos no deben penalizar)
- **Input:** 5 GIF animados; `_formato_imagen` los clasifica gif — no penaliza (ok); verificar que no aparezcan como «PNG sin WebP» (solo se dispara con png presente).
- **Esperado:** Sin penalización por GIF; test de regresión.
- **Severidad:** Bajo
- **Validación:** Test unitario de `_formato_imagen` con gif/svg/avif.

### C23. Sitio con imágenes en `srcset` con URL parametrizadas (`?w=400&h=300`)
- **Input:** `src="img.jpg?w=800&h=600"` → `_formato_imagen` detecta `.jpg` (ok) — pero `data:` no; variante: URL con `?format=webp` sin extensión.
- **Esperado:** Detectar formato por query/Content-Type cuando no hay extensión; no clasificar «otro» todo.
- **Severidad:** Bajo
- **Validación:** Parsear query params `format`/`fm`; HEAD para content-type de muestra.

### C24. Sitio con enlaces CTA con texto genérico en mayúsculas o con tildes raras
- **Input:** CTA «LEER MÁS» (mayúsculas) — `l["text"].lower()` lo matchea (ok). Variante «leer mas» sin tilde → no matchea (BUG REAL menor: keyword con tilde).
- **Esperado:** Normalizar acentos en la detección de CTAs.
- **Severidad:** Bajo
- **Validación:** Normalización Unicode (NFD y quitar diacríticos) en keywords y textos.

### C25. Sitio con CTA real en botón `<button>` (no en `<a>`)
- **Input:** Botón «Comprar ahora» como `<button>` (form) sin `<a>`.
- **Esperado:** El análisis solo mira `<a>` para CTAs (BUG REAL: `_extraer_enlaces` no mira buttons) → falso negativo de CTAs en sitios con botones.
- **Severidad:** Medio
- **Validación:** Incluir `<button>` y `input[type=submit]` con texto en la detección de CTAs.

### C26. Sitio con testimonios marcados con `<blockquote>` (la detección de confianza funciona)
- **Input:** `blockquote` con testimonios; `_evaluar_conversion` suma confianza (ok). Variante: testimonios en `div class="testimonial"`.
- **Esperado:** `soup.find_all(["blockquote", ".testimonial", ".review"])` — el selector `.testimonial` en find_all **no funciona como selector CSS** (BUG REAL: `find_all` recibe strings literal, no selectores CSS — busca tags llamados «.testimonial»).
- **Severidad:** Medio
- **Validación:** Usar `soup.select('.testimonial, .review, blockquote')`.

### C27. Sitio con la palabra «garantía» solo en el footer legal («sin garantía»)
- **Input:** Footer con «Este servicio no ofrece garantía» → `"garant" in html_text` suma confianza (falso positivo de confianza).
- **Severidad:** Bajo
- **Validación:** Contextualizar (positivo/negativo) o exigir proximidad a CTA.

### C28. Sitio con contador de visitas o texto «comprar» en menú de admin oculto
- **Input:** Texto «comprar» aparece en un menú desplegable oculto (display:none) → CTA falso.
- **Severidad:** Bajo
- **Validación:** Excluir contenido oculto (ver A27).

### C29. Sitio con `robots noindex` en páginas internas pero la home indexable — análisis solo de home
- **Input:** Análisis de la home (indexable) ok; el cliente espera «todo el sitio».
- **Esperado:** El reporte aclara que se audita la URL puntual (o el modo multipágina); no vender «auditoría del sitio» con una sola página.
- **Severidad:** Medio
- **Validación:** Copys del reporte aclarando alcance; destacar el modo multipágina.

### C30. Multipágina con límite de 5 links internos — los links elegidos son de la nav (no representativos)
- **Input:** `_extraer_links_internos` toma los primeros links (nav: Inicio, Productos, Contacto) y no las páginas de contenido.
- **Esperado:** La muestra multipágina representa el sitio (priorizar páginas de contenido, no nav).
- **Severidad:** Medio
- **Validación:** Priorizar links con texto largo/páginas de contenido y deduplicar nav.

### C31. Multipágina con `depth` muy alto (p. ej. 20) — crawler interno masivo
- **Input:** `depth=20` → `_analizar_multipagina` analiza 19 páginas internas secuencialmente (BUG REAL: sin límite de páginas totales ni de tiempo → DoS/agotamiento de quota para el operador).
- **Esperado:** Límite total de páginas (p. ej. 10) y timeout global; validar `depth` en backend (máx 5).
- **Severidad:** Alto
- **Validación:** Clamp `depth = min(max(depth,1),5)` y límite de páginas en `_analizar_multipagina`.

### C32. Sitio con `www` vs sin `www` — dos análisis dan resultados distintos
- **Input:** `sitio.com` redirige a `www.sitio.com`; el scorecard usa la URL final para PSI (ok) pero el reporte muestra la URL original en `url`.
- **Esperado:** Consistencia entre URL analizada, URL final y canonical; sin doble conteo de redirects en PSI.
- **Severidad:** Bajo
- **Validación:** Test con redirección www/no-www.

### C33. Sitio con error 500 en una ruta interna pero 200 en home — multipágina ignora errores
- **Input:** `_analizar_multipagina` hace `continue` silencioso en sub-páginas con error → el promedio oculta páginas rotas.
- **Esperado:** Reportar «N páginas no se pudieron auditar (error X)» en vez de omitirlas silenciosamente.
- **Severidad:** Medio
- **Validación:** Acumular `errores` de sub-páginas y mostrarlos en el reporte.

### C34. Sitio con página de producto con `noindex` (páginas filtradas) — SEO del catálogo
- **Input:** Catálogo con páginas de filtro `noindex` (patrón correcto); el análisis de esas URLs las penaliza como «no indexables».
- **Esperado:** Aviso «página no indexable — el score SEO es informativo» (ver A31).
- **Severidad:** Bajo
- **Validación:** Tratar `noindex` como informativo, no penalizable.

### C35. Sitio con lazy loading implementado por JS (lazysizes) — el HTML no tiene `loading=`
- **Input:** Imágenes con `data-src` (lazysizes) y `class="lazyload"`, sin `loading="lazy"` nativo.
- **Esperado:** El análisis los cuenta como «sin lazy» (falso positivo: SÍ están optimizadas por JS).
- **Severidad:** Medio
- **Validación:** Reconocer `data-src`/`class=lazyload`/`data-lazy` como lazy ya aplicado.

### C36. Sitio con `loading="lazy"` en el 100% incluyendo hero (mala práctica pero presente)
- **Input:** Hero con `loading="lazy"` (el cliente lo puso mal).
- **Esperado:** El análisis NO lo penaliza (está «lazy») pero debería sugerir «el hero no debería ser lazy» (mejora de calidad).
- **Severidad:** Bajo
- **Validación:** Hallazgo opcional «hero con lazy — considerar eager».

### C37. Sitio con título duplicado exacto en todas las páginas (mismo title en home y category)
- **Input:** Home y categorías con el mismo title.
- **Esperado:** El análisis de una sola página no lo detecta (no cruza páginas) — en modo multipágina debería marcar «títulos duplicados entre páginas».
- **Severidad:** Bajo
- **Validación:** En `_analizar_multipagina`, comparar titles entre páginas.

### C38. Sitio con URLs de imágenes de otro dominio caído (CDN roto) — imágenes 404
- **Input:** Imágenes apuntan a CDN caído (404); el análisis las cuenta como presentes (no verifica).
- **Esperado:** Hallazgo «N imágenes rotas (404)» (no implementado — falso negativo).
- **Severidad:** Medio
- **Validación:** HEAD/GET de muestra de imágenes (límite de N) y reportar rotas.

### C39. Sitio con `favicon` ausente o roto — no auditado
- **Input:** Sin favicon ni `apple-touch-icon`.
- **Esperado:** Hallazgo menor «falta favicon» (no implementado — falso negativo menor).
- **Severidad:** Bajo
- **Validación:** Chequeo de favicon/icon links.

### C40. Sitio con velocidad excelente pero el reporte igual recomienda lazy porque faltaba en 1 imagen
- **Input:** 20 imágenes, 1 sin lazy; el gate actual (>30%) no dispara (correcto) — test de regresión del umbral.
- **Esperado:** Sin recomendación si < 30% (ya correcto); verificar que la recomendación de lazy exige `> 50%` (BUG REAL menor: `_generar_recomendaciones` usa `> 0.5` pero `_evaluar_rendimiento` penaliza desde `> 30%` — inconsistencia entre penalización y recomendación).
- **Severidad:** Bajo
- **Validación:** Alinear umbrales entre evaluador y generador de recomendaciones.

---

# D. Casos de negocio / reputación (30 casos)

### D1. Sitio de salud: el plugin agrega CTA flotante «Suscribite gratis» sobre el sitio de una clínica
- **Input:** Clínica con datos sensibles; el plugin inyecta branding de «Web Analyzer» (CTA/trust bar) sobre el sitio del cliente.
- **Esperado:** El plugin NO agrega elementos de marca propios del SaaS sobre sitios de terceros sin consentimiento explícito (riesgo reputacional/legal, y el cliente nunca lo pidió).
- **Severidad:** Crítico
- **Validación:** Toggle «marca del producto» por defecto OFF; consentimiento en el flujo de descarga.

### D2. Cliente no técnico instala el plugin y rompe el sitio — instrucciones de FTP inútiles
- **Input:** Fatal error; las «INSTRUCCIONES DE SEGURIDAD» del plugin dicen «entrá por FTP/SFTP y renombrá la carpeta» — para un cliente sin FTP.
- **Esperado:** Instrucciones de rollback por wp-admin (Plugins → desactivar) primero; FTP solo como alternativa; link a soporte destacado.
- **Severidad:** Alto
- **Validación:** Mejorar el texto del plugin; agregar link directo `plugins.php` y soporte.

### D3. El análisis tarda 45 s (PSI lento) pero la landing promete «30 segundos»
- **Input:** PSI tarda 30 s + crawler 15 s; la UI muestra spinner sin ETA.
- **Esperado:** ETA honesta («puede tardar hasta 1 min»); no romper la promesa de marketing (30 s) con tiempos de 60 s.
- **Severidad:** Medio
- **Validación:** Mostrar progreso por etapas (fetch → extracción → PageSpeed) en la UI.

### D4. El plugin se descarga «gratis» pero la UI muestra precio ARS 12.000 (flujo obsoleto)
- **Input:** `demo-cta` del render muestra «Comprar por ARS 12.000»; el backend dice «Todas las soluciones libres (sin pasarela de pago)» — **contradicción de producto**.
- **Esperado:** UI coherente con el backend: o se cobra o se muestra gratis; hoy promete cobro que no existe (confusión y posible reclamo).
- **Severidad:** Alto
- **Validación:** Unificar copy de pricing con el flujo real (feedback, no pago).

### D5. El email de lead llega con un link roto (`/report/` vs `/r/`)
- **Input:** `api_lead` arma `https://webanalyzer.com.ar/report/{hash}` pero la ruta real es `/r/{hash}` (BUG REAL) → el cliente recibe un reporte inaccesible → pierde confianza y el lead se pierde.
- **Severidad:** Crítico
- **Validación:** Usar la ruta real (`/r/`) o generar el link desde el router.

### D6. El email de lead usa la URL del sitio analizado si no hay report_hash — enlace a sitio ajeno
- **Input:** Sin `report_hash`, el email dice «Ver el reporte completo acá: {url}` — apunta al sitio del cliente, no a un reporte (confuso).
- **Severidad:** Medio
- **Validación:** Siempre generar report_hash server-side y usar el link real.

### D7. Email de lead sin validación de formato (email inválido) — silencio o rebote
- **Input:** `email = "no-es-un-mail"` → `send_email` falla (rebote) o se envía; no hay validación ni mensaje de error al usuario.
- **Severidad:** Medio
- **Validación:** Validar formato email y devolver error claro; loguear rebotes.

### D8. Un competidor analiza el sitio del cliente y le llega el reporte del competidor
- **Input:** Cualquiera puede analizar cualquier sitio y el reporte compartido (`/r/{hash}`) es público por URL determinística (`sha256(url)[:12]` — BUG REAL: predecible).
- **Esperado:** Los reportes de un sitio no deben ser adivinables/enumerables; si el cliente ve su reporte filtrado, daño de confianza.
- **Severidad:** Alto
- **Validación:** `report_hash` aleatorio (secrets.token_hex) en vez de hash del URL; auth para ver reportes propios.

### D9. El historial de análisis es global y público (`/api/history` sin filtro por usuario)
- **Input:** `api_history` devuelve TODOS los análisis de todos los usuarios (BUG REAL: `listar_analisis()` global) → un usuario ve las URLs que auditaron otros (datos de negocio ajenos).
- **Severidad:** Crítico
- **Validación:** Filtrar por `user_id`; solo el admin ve todo.

### D10. Sitio de un cliente del rubro legal — el análisis guarda el HTML completo en disco
- **Input:** `_guardar_analisis` persiste `html_raw`? No — lo excluye del JSON, pero el JSON guarda `meta`, `forms`, `imagenes`, `enlaces` (datos de terceros) sin consentimiento ni TTL.
- **Esperado:** Retención mínima y documentada; consentimiento para guardar datos de sitios de terceros (política de privacidad).
- **Severidad:** Alto
- **Validación:** TTL/purga de `analisis/`; disclaimer en la política; excluir valores de inputs.

### D11. Cliente con poco conocimiento técnico descarga el plugin y NO sabe qué cambió en su sitio
- **Input:** El plugin aplica 7 cambios silenciosamente (metas, H1, lazy, defer, CTA, newsletter, trust bar).
- **Esperado:** Al activar, un notice admin lista exactamente qué se cambió y cómo revertir cada fix individualmente.
- **Severidad:** Alto
- **Validación:** Página de «qué cambió» (changelog del plugin) + toggles por fix (ver B34).

### D12. El plugin se activa en un sitio y el cliente ve el doble de newsletter (el que ya tenía + el del plugin)
- **Input:** (ver B12) — además de roto, daña la percepción: el cliente cree que el SaaS no auditó bien su sitio.
- **Severidad:** Alto
- **Validación:** El reporte debe decir «tu sitio ya tiene newsletter — no incluimos ese fix».

### D13. Cliente analiza su sitio, el score es 4/10, y el plugin no cambia el score real después de instalarlo
- **Input:** El cliente instala el plugin y espera «mejorar el score»; el scorecard no se re-mide automáticamente.
- **Esperado:** Ofrecer re-análisis tras instalar (CTA «volvé a analizar»); mostrar antes/después.
- **Severidad:** Medio
- **Validación:** Flujo de re-análisis post-instalación con comparación de scores.

### D14. El score de un sitio cambia drásticamente según la hora del día (pico vs valle)
- **Input:** PSI varía 3 puntos entre 9 AM y 3 AM.
- **Esperado:** El reporte marca la hora de medición y advierte de variabilidad; no presentar un score puntual como «el» score.
- **Severidad:** Medio
- **Validación:** Timestamp visible + nota de variabilidad.

### D15. Un cliente en el rubro financiero recibe la recomendación «agregá un newsletter»
- **Input:** Sitio de un banco/asesor financiero sin newsletter (regulado, no corresponde).
- **Esperado:** Recomendaciones contextuales por vertical (ver C1) — en verticales reguladas, no sugerir captura de emails masiva.
- **Severidad:** Medio
- **Validación:** Heurística de vertical + reglas por vertical.

### D16. El plugin genera un ZIP con nombre basado en el dominio — para dos clientes iguales (multitienda)
- **Input:** Dos tiendas `marca.com.ar` y `marca.com` → `safe_domain` = `marca_com_ar` y `marca_com` (distintos, ok); pero `marca.com` y `www.marca.com` → igual (`marca_com`) → **el ZIP del segundo pisa al primero** en `output/` (BUG REAL: `_guardar_analisis` escribe `output/{safe_domain}_optimizer.zip` con nombre colisionante).
- **Severidad:** Alto
- **Validación:** Nombre único con hash/timestamp en `output/`; el `nombre` mostrado puede quedarse legible.

### D17. El reporte dice «SEO: 9/10» pero el sitio tiene el title duplicado en todas las páginas (no medido)
- **Input:** (ver C37) — el cliente confía en un score alto que oculta un problema real → daño de confianza cuando lo descubre.
- **Severidad:** Medio
- **Validación:** Aclarar alcance de cada score («medido en esta página»).

### D18. Cliente analiza un sitio que NO es suyo (le gusta el diseño del competidor)
- **Input:** El SaaS permite analizar cualquier URL y descargar «el plugin del competidor» — funcionalidad legítima de auditoría pero roza scraping de diseño.
- **Esperado:** Política de uso documentada (no reclamar el plugin sobre sitios de terceros); sin acción técnica, pero disclaimer en términos.
- **Severidad:** Bajo
- **Validación:** Términos de servicio con límites de uso.

### D19. El plugin se genera para un sitio Wix/Squarespace (no WordPress) igual
- **Input:** `_generar_soluciones` genera el plugin WP «siempre, para cualquier sitio» (BUG REAL: comentario en código) — un cliente con Wix recibe un ZIP inútil y cree que «su solución» es esa.
- **Esperado:** Solo ofrecer el plugin WP si se detectó WordPress; si no, ofrecer el snippet/patch correspondiente (y Shopify si corresponde).
- **Severidad:** Crítico
- **Validación:** Gate por `tech` (WordPress) antes de generar el ZIP; UX con mensaje claro.

### D20. Cliente con Wix instala el ZIP «optimizer» en un hosting WordPress que no es el suyo — confusión total
- **Input:** (derivado de D19) — el flujo permite descargar cosas inaplicables sin aviso.
- **Severidad:** Alto
- **Validación:** Al descargar, confirmar «tu sitio es WordPress?» y guiar según respuesta.

### D21. El formulario del plugin pide email pero no dice qué se hace con él (consentimiento)
- **Input:** El newsletter del plugin no tiene checkbox de consentimiento ni política (Ley 25.326 Argentina / GDPR para clientes UE).
- **Esperado:** Consentimiento explícito y aviso de privacidad junto al form.
- **Severidad:** Alto
- **Validación:** Checkbox requerido + link a política; y como B28, el form debe procesar (hoy pierde datos).

### D22. El cliente usa el plugin y luego de desinstalarlo su meta description vuelve a la vieja (bien) pero Google sigue mostrando la nueva (mal)
- **Input:** Cambios de meta ya indexados por Google; al desinstalar, el snippet viejo reaparece tras re-crawl (comportamiento esperado de SEO — el cliente no lo entiende).
- **Esperado:** Documentación/aviso: «los cambios SEO tardan en reflejarse en Google; no reviertas a la ligera».
- **Severidad:** Bajo
- **Validación:** Sección FAQ en el reporte.

### D23. Soporte: no hay canal de reporte de bugs dentro del flujo (solo email hardcodeado)
- **Input:** `soporte@delmonteanalitica.com` hardcodeado en 4 lugares del plugin; sin ticket/estado.
- **Esperado:** Canal de soporte real con SLA; el email está bien como fallback.
- **Severidad:** Bajo
- **Validación:** Verificar que el email existe y responde; agregar link a FAQ.

### D24. La auditoría marca «accesibilidad 9/10» en un sitio que falla contraste y teclado — riesgo legal WCAG
- **Input:** (ver C13/C14) — un cliente en un país con requisitos de accesibilidad usa el reporte como certificación y queda expuesto.
- **Esperado:** El reporte aclara explícitamente «auditoría parcial, no certificación WCAG».
- **Severidad:** Alto
- **Validación:** Disclaimer legal en el reporte y en la descarga.

### D25. El «monitoreo de URLs» no tiene scheduler visible — la función puede ser cosmética
- **Input:** `api_monitor` guarda URLs y scores, pero no se ve ningún cron/reproceso que re-analice periódicamente (BUG REAL potencial: la promesa «URLs en monitoreo» sin backend que monitoree).
- **Esperado:** O implementar el cron real, o quitar la feature; hoy es una promesa vacía → daño reputacional.
- **Severidad:** Alto
- **Validación:** Implementar job (APScheduler/cron) o eliminar la UI de monitoreo.

### D26. Cliente pagó el tier (antes) y ahora todo es gratis — percepción de estafa inversa
- **Input:** El backend comenta «Feedback (reemplaza compras)»; usuarios que pagaron ARS 12.000 antes ven todo gratis → reclamos.
- **Esperado:** Política de transición documentada (créditos/refunds) — caso de negocio, no de código.
- **Severidad:** Medio
- **Validación:** Comunicación de cambio de modelo; tier legacy con beneficio.

### D27. Análisis de un sitio con contenido ilegal/abusivo vía API anónima — uso indebido
- **Input:** `api_analyze` anónima sin términos; cualquiera puede usarla como proxy HTTP con UA de navegador (los headers se reenvían) — abuso/uso malicioso.
- **Esperado:** Términos, límites por IP (ya hay rate limit) y detección de abuso; el UA es de Chrome real → el servidor objetivo ve tráfico de «navegador».
- **Severidad:** Medio
- **Validación:** ToS + bloqueo por comportamiento; UA identificable del producto.

### D28. El `X-User-Token` se manda por query string (`?user_token=`) en algunos flujos
- **Input:** `check_auth` acepta `user_token` en query → tokens en logs de proxy/analytics (fuga de sesión).
- **Severidad:** Alto
- **Validación:** Solo header `X-User-Token`; nunca en query.

### D29. El cliente recibe el reporte por email desde `no-reply@webanalyzer.com.ar` con el dominio correcto pero sin firma de remitente válida (SPF/DKIM)
- **Input:** Ferozo sin SPF/DKIM configurado → los emails caen en spam → el lead cree que el servicio no funciona.
- **Severidad:** Alto
- **Validación:** Configurar SPF/DKIM/DMARC y verificar con tool.

### D30. Si el análisis de un sitio tarda o falla a mitad, el cliente no puede reintentar desde el reporte
- **Input:** Timeout en PSI → `errores` parciales; la UI muestra scorecard parcial sin explicar.
- **Esperado:** «Análisis parcial: PageSpeed no respondió» con botón «reintentar métricas».
- **Severidad:** Medio
- **Validación:** Estado parcial explícito + retry de PSI.

---

# E. Seguridad (40 casos)

### E1. SSRF — DNS rebinding (la IP pública en el primer lookup, privada en el segundo)
- **Input:** Dominio atacante que alterna `1.2.3.4` (público) y `169.254.169.254` (metadata cloud) entre resoluciones; `_is_public_url` resuelve y valida, luego `requests` re-resuelve (TOCTOU — BUG REAL).
- **Esperado:** La conexión usa exactamente la IP validada (pin a IP + Host header) o se bloquea el rebinding.
- **Severidad:** Crítico
- **Validación:** Resolver una vez, conectar a la IP validada con `Host`/SNI; o validar la IP en la conexión real.

### E2. SSRF — IPv6 mapeada a IPv4 (`::ffff:127.0.0.1`) y formas alternas (`127.1`, `2130706433` decimal)
- **Input:** `http://[::ffff:127.0.0.1]/`, `http://127.1/`, `http://2130706433/` (127.0.0.1 en decimal).
- **Esperado:** Todas bloqueadas (hostname `127.1` no matchea `127.` — BUG REAL menor: `127.1` resuelve a 127.0.0.1 y `getaddrinfo` da IP privada → bloqueado por IP, ok; pero el decimal `2130706433` también resuelve a 127.0.0.1 → IP check lo cubre).
- **Severidad:** Alto
- **Validación:** Test matrix de representaciones IP; pin IP tras validar.

### E3. SSRF — redirect a host interno vía `Location` con `//` o codificación
- **Input:** `Location: //169.254.169.254/latest/meta-data/` o `Location: http://127.0.0.1%00.evil.com` (parsing inconsistente).
- **Esperado:** `_safe_get` re-valida cada redirect (ya lo hace) — test de bypass por parsing (`%00`, punycode, `0x7f000001`).
- **Severidad:** Alto
- **Validación:** Fuzz de parsing de URL en `_is_public_url` (punycode, hex IP, octal, userinfo).

### E4. SSRF — URL con credenciales y host engañoso (`http://169.254.169.254@public.com`)
- **Input:** Userinfo con IP interna antes del `@`.
- **Esperado:** `urlparse().hostname` da `public.com` (host real) → pasa; requests conecta a public.com → sin bypass — confirmar con test.
- **Severidad:** Medio
- **Validación:** Test de regresión; documentar que el hostname real es el que se valida.

### E5. SSRF — protocolos no-HTTP (`file://`, `gopher://`, `dict://`, `ftp://`)
- **Input:** `file:///etc/passwd`, `gopher://` — `_is_public_url` bloquea por scheme (ok); verificar que `_safe_get` nunca permite otros schemes (redirects incluidos).
- **Severidad:** Alto
- **Validación:** Test de schemes; `urljoin` de redirects relativos no debe derivar a scheme distinto.

### E6. SSRF — puertos no estándar abiertos (Redis 6379, Elasticsearch 9200 en hosts públicos)
- **Input:** `http://sitio-publico.com:9200/` — IP pública válida, puerto con servicio interno del atacante.
- **Esperado:** Política de puertos (solo 80/443/8080/8443) o aceptar el riesgo documentado; hoy acepta cualquier puerto.
- **Severidad:** Medio
- **Validación:** Whitelist de puertos; test 9200/6379/22.

### E7. Gzip bomb / página de 500 MB que agota la memoria del worker
- **Input:** URL que sirve HTML comprimido 100:1 (gzip bomb) o 200 MB plano; `resp.text` lo materializa en memoria (BUG REAL: sin límite de tamaño).
- **Esperado:** Límite de bytes (p. ej. 10 MB) con aborto controlado y error claro.
- **Severidad:** Crítico
- **Validación:** Stream con `iter_content` y corte por tamaño; test con gzip bomb de juguete.

### E8. DoS — `depth` ilimitado en `/api/analyze` (crawl masivo)
- **Input:** `POST /api/analyze {"url": "...", "depth": 999}` → crawlea cientos de páginas secuencialmente (ver C31) — agota quota, CPU y storage del operador.
- **Severidad:** Alto
- **Validación:** Clamp en backend + rate limit por usuario/IP ya existente pero ajustado al costo (5/min es poco para depth alto).

### E9. DoS — muchos análisis de la misma URL grande (disk fill)
- **Input:** Repetir análisis de un sitio grande → `_guardar_analisis` escribe un JSON por corrida (BUG REAL: sin rotación/purga) → disco lleno.
- **Severidad:** Alto
- **Validación:** Purga por antigüedad (TTL) y límite de archivos por dominio.

### E10. Abuso del email de leads — `api_lead` SIN rate limit (open email relay)
- **Input:** `POST /api/lead {"email": "victima@gmail.com", "url": "..."}` repetido → el servidor envía emails a cualquier dirección (BUG REAL: endpoint sin `@limiter.limit` y sin validación) → spam/fishing usando el dominio del SaaS.
- **Severidad:** Crítico
- **Validación:** Rate limit estricto por IP (p. ej. 3/hora), validación de email, CAPTCHA/honeypot, y límite diario global.

### E11. Email header injection vía `email` con CRLF en `/api/lead`
- **Input:** `email = "a@b.com\r\nBcc: spam@x.com"` → `msg["To"] = to` (BUG REAL potencial: header injection en To/Bcc).
- **Severidad:** Alto
- **Validación:** `email.utils.parseaddr`/validación estricta de formato antes de armar el mensaje; nunca interpolar el input directo.

### E12. Enumeración de reportes compartidos por hash determinístico
- **Input:** `report_hash = sha256(url)[:12]` — se puede enumerar/adivinar el hash de un sitio conocido y ver su scorecard público (BUG REAL, ver D8).
- **Severidad:** Alto
- **Validación:** Hash aleatorio + opcional de privado.

### E13. Exposición de `X-User-Token` en query strings y logs
- **Input:** (ver D28) — tokens en logs de acceso/proxy.
- **Severidad:** Alto
- **Validación:** Solo header; sanitizar logs.

### E14. Tokens de sesión sin expiración efectiva o rotación en logout
- **Input:** `token_expires` existe; verificar: ¿hay logout que invalide el token? Si no, un token robado vale para siempre.
- **Severidad:** Medio
- **Validación:** Endpoint de logout que borre/rota el token; TTL razonable.

### E15. Brute-force de login sin lockout (solo rate limit 10/min por IP)
- **Input:** Fuerza bruta distribuida (muchas IPs) contra `/api/auth/login` — el rate limit por IP no frena ataques distribuidos; falta lockout por cuenta.
- **Severidad:** Medio
- **Validación:** Lockout por email después de N fallos (independiente de IP) + retraso exponencial.

### E16. Registro sin verificación de email (cuentas falsas)
- **Input:** Registrar con `a@b.c` (dominio inexistente) — la cuenta queda activa; el tier free se puede abusar.
- **Severidad:** Bajo
- **Validación:** Verificación de email opcional; mínimo validar formato y dominio MX.

### E17. Password policy débil (mín 6 caracteres, sin complejidad)
- **Input:** `password="123456"` aceptado (minlength 6 en el front; ¿backend también?).
- **Severidad:** Bajo
- **Validación:** Policy mínima (8 chars) en backend (validar en `create_user`).

### E18. XSS reflejado en el render vía datos del sitio analizado
- **Input:** Un sitio analizado con `og:title` = `<script>alert(1)</script>`; el render muestra `meta.title` en el DOM.
- **Esperado:** Escape en el front (React/vars del template) — test de regresión; el `esc_attr` del plugin solo aplica al generar el PHP.
- **Severidad:** Alto
- **Validación:** Prueba con payloads `<script>`, `"><img onerror>`, `{{7*7}}` (templating) en title/description del sitio analizado; verificar escape en render y en JSON.

### E19. XSS almacenado vía feedback/comentario (se renderiza para el admin?)
- **Input:** `POST /api/feedback` con `comentario` que se muestra en un panel admin sin escape.
- **Severidad:** Alto
- **Validación:** Escapar en toda renderización de comentarios; validar longitud.

### E20. Inyección PHP en el plugin generado vía `site_name`/`site_url` del sitio analizado
- **Input:** Sitio atacante con `og:site_name` = `x */ system('id'); /*` — el generador interpola sin escapar en el `/* */` docblock (BUG REAL en `_generar_plugin_wordpress`) → **RCE en el WordPress del cliente cuando instala el plugin**.
- **Severidad:** Crítico
- **Validación:** Escapar/eliminar `*/`, `<?php`, comillas y backslashes de toda interpolación en el PHP generado; o usar `json_encode`/heredoc seguro; test con payloads.

### E21. Inyección PHP vía `site_url` (Plugin URI e instrucciones)
- **Input:** `url` con `*/ eval(...) /*` en la URL final del sitio → interpola en `Plugin URI: {site_url}` (BUG REAL, mismo vector que E20).
- **Severidad:** Crítico
- **Validación:** Sanear URL en el generador; nunca interpolar la URL cruda en código PHP.

### E22. Inyección PHP vía `safe_domain` — verificar sanitización
- **Input:** Dominio `evil.com" ; system('x'); //` → `re.sub(r"[^a-zA-Z0-9_]", "_", dominio)` lo sanitiza (ok) — test de regresión con dominios exóticos (punycode, `xn--`).
- **Severidad:** Medio
- **Validación:** Test de `safe_domain` con payloads.

### E23. Zip Slip en el ZIP generado
- **Input:** `safe_domain` sanitizado + `writestr(f"{plugin_dir}/{file}")` — sin `../` posible (ok); test de regresión si el generador cambia.
- **Severidad:** Bajo
- **Validación:** Test que verifique que ningún entry del zip escapa del directorio del plugin.

### E24. Inyección en `filename` de descarga — validado pero testear variantes
- **Input:** `filename = "../../etc/passwd"` → regex `^[a-zA-Z0-9_.\-]+$` lo rechaza (ok); `filename = "..%2f..%2f"` → decodificado por el framework? `os.path.basename` + resolve + prefix check cubre — test de doble-encoding.
- **Severidad:** Alto
- **Validación:** Test matrix de traversal (`..`, `%2e%2e`, backslash, `....//`).

### E25. Path traversal en `/api/download` vía `report_hash` o path absoluto
- **Input:** `filename` con path absoluto `C:\Windows\win.ini` — regex lo bloquea (ok).
- **Severidad:** Medio
- **Validación:** Test de path absoluto y UNC (`\\server\share`).

### E26. SSRF en PageSpeed Insights — la URL se inyecta sin encode (parámetros propios)
- **Input:** URL analizada `https://site.com/?key=MI_KEY_GOOGLE` → `api_url = ...?url={url}` (BUG REAL) → el `key=` del sitio sobreescribe/contamina el key de PSI o rompe la llamada.
- **Severidad:** Alto
- **Validación:** `urllib.parse.quote(url)` antes de interpolar.

### E27. Consumo de quota de Google PSI por terceros (abuso del key)
- **Input:** (derivado de E26) — un atacante puede hacer que el SaaS consuma su propia key de PSI con URLs masivas (quota agotada → todos los clientes pierden PSI).
- **Severidad:** Medio
- **Validación:** Encode + cache de resultados PSI por URL.

### E28. CORS demasiado abierto en algún endpoint
- **Input:** Verificar `Access-Control-Allow-Origin` en respuestas a `Origin: http://evil.com` (whitelist actual ok) — test de regresión; `api_lead`/`api_analyze` anónimos con credenciales no deben permitir CORS desde orígenes no listados.
- **Severidad:** Bajo
- **Validación:** Test CORS con orígenes no listados (debe omitir el header).

### E29. Rate limit `memory://` — se resetea en restart y no funciona multi-worker
- **Input:** Render con 2 workers → el límite por IP se duplica o se resetea (BUG REAL: `storage_uri="memory://"` es por proceso).
- **Severidad:** Medio
- **Validación:** Storage compartido (Redis) o aceptar y documentar; al menos consistente en 1 worker.

### E30. Payloads de XSS/inyección en la URL analizada (query con `<script>`)
- **Input:** `https://sitio.com/?q=<script>alert(1)</script>` — el HTML reflejado del sitio entra a `html_raw` y se guarda/loguea; si algún día se renderiza → XSS.
- **Severidad:** Medio
- **Validación:** Nunca renderizar `html_raw`; escapar todo output del análisis.

### E31. Inyección en el log vía URL (log injection / log forging)
- **Input:** URL con `\n` y contenido falso en el log → `log.info(f"url={url}")` (BUG REAL: CRLF en URL entra al log).
- **Severidad:** Bajo
- **Validación:** Sanear/escapar CRLF en logs; formato estructurado JSON.

### E32. El `User-Agent` rotativo de Chrome real facilita abuso del producto como proxy anónimo
- **Input:** (ver D27) — UA de Chrome + Accept de navegador → el servicio puede usarse para escanear sin identificarse.
- **Severidad:** Medio
- **Validación:** UA identificable (`WebAnalyzer/1.0 (+https://webanalyzer.com.ar)`) en una cabecera adicional `X-WebAnalyzer`, manteniendo compatibilidad.

### E33. Información del servidor en errores (tracebacks en respuesta)
- **Input:** `api_register` con excepción inesperada → `{"error": f"Error interno: {e}"}` (BUG REAL: expone mensaje de excepción crudo, posible leak de SQL/stack).
- **Severidad:** Medio
- **Validación:** Errores genéricos + `trace_id`; detalle solo en logs.

### E34. SQL injection — verificar parametrización en database.py
- **Input:** Todas las queries usan `?`/`%s` parametrizados (revisado: `_q()` + params — ok); test de fuzz en email/url/report_hash.
- **Severidad:** Bajo
- **Validación:** Test de fuzz; auditoría periódica.

### E35. IDOR en monitoreo — `DELETE /api/monitor?id=N` valida propiedad
- **Input:** `delete_monitored_url(id, user_id)` con user_id (verificar que filtra por usuario — BUG REAL potencial si no filtra).
- **Severidad:** Alto
- **Validación:** Test IDOR: usuario A borra el monitoreo de B.

### E36. IDOR en reportes compartidos — cualquier usuario puede ver cualquier `/r/{id}` (diseño público, pero verificar que no filtre datos del analizador)
- **Input:** El reporte compartido contiene solo scorecard (ok); verificar que NO incluya `html_raw`, emails, ni datos internos.
- **Severidad:** Medio
- **Validación:** Auditar `create_shared_report` para excluir datos sensibles del dict compartido.

### E37. El plugin generado guarda el email del form en ningún lado pero el form existe → posible phishing de datos si un atacante lo explota
- **Input:** (ver B28) — el form sin handler es además un vector: un atacante podría inyectar un handler vía el mismo flujo (E20) — encadenar.
- **Severidad:** Alto
- **Validación:** Fix E20 primero; el form sin handler no debe existir.

### E38. Dependency supply chain — `requests`, `bs4`, `flask` sin pinning en requirements
- **Input:** Revisar `requirements.txt`: si no hay versiones pinneadas, un deploy nuevo puede traer dependencias con CVE.
- **Severidad:** Bajo
- **Validación:** Pinear versiones + `pip-audit` en CI.

### E39. El `.env` contiene SMTP password en el repo/directorio expuesto
- **Input:** `SMTP_PASS` con default hardcodeado en el código (`os.environ.get("SMTP_PASS", "25YmQhbaWJ")`) — BUG REAL: credencial Ferozo en el fuente; y `.env` real presente en el directorio.
- **Severidad:** Crítico
- **Validación:** Quitar default del código; rotar la credencial; `.env` en `.gitignore` y fuera del tree web.

### E40. Cabeceras de seguridad faltantes en las respuestas del SaaS
- **Input:** Respuestas sin `X-Content-Type-Options: nosniff`, `X-Frame-Options`, CSP; el render con datos del sitio analizado (E18) eleva el riesgo.
- **Severidad:** Medio
- **Validación:** Middleware de seguridad (nosniff, frame-ancestors, CSP básica); test de headers.

---

# Resumen ejecutivo — Top 10 a corregir primero

| # | Bug | Severidad | Función |
|---|-----|-----------|---------|
| 1 | Inyección PHP en el plugin generado (`*/` en site_name/url) → RCE en el sitio del cliente | Crítico | `_generar_plugin_wordpress` |
| 2 | `api_lead` sin rate limit → open email relay / spam masivo | Crítico | `app.py: api_lead` |
| 3 | SSRF por DNS rebinding / TOCTOU en `_is_public_url` | Crítico | `analyzer.py: _is_public_url` |
| 4 | Gzip bomb / respuesta sin límite de tamaño → OOM del worker | Crítico | `analyzer.py: _safe_get` |
| 5 | `api_history` global sin filtro por usuario (fuga de URLs ajenas) | Crítico | `app.py: api_history` |
| 6 | Reportes compartidos con hash determinístico (`sha256(url)[:12]`) | Alto | `app.py: api_analyze` |
| 7 | Regex de lazy loading que rompe `<img>` multilínea y strings JS | Crítico | Plugin `_optimize_output` |
| 8 | El plugin borra metas de Yoast/RankMath y duplica newsletter/CTA | Crítico | Plugin `_optimize_output` |
| 9 | Falso diagnóstico masivo en SPAs (auditoría sobre HTML crudo vacío) | Crítico | `analyzer.py: analizar` |
| 10 | SMTP password hardcodeado como default en el código | Crítico | `app.py: SMTP_PASS` |

**Cobertura:** A=40 sitios atípicos/rotos · B=50 plugin destructivo · C=40 falsos positivos/negativos ·
D=30 negocio/reputación · E=40 seguridad. Total **200 casos**.
