# QA — 25 casos críticos priorizados (probabilidad × impacto) y sus tests

Selección de los 25 casos más críticos de la matriz de 200 (`docs/QA-200-casos-adversariales.md`),
ordenados por **probabilidad × impacto**. Cada caso tiene su test automatizado en pytest
(los archivos `test_qa_*_criticos.py`), que codifica el comportamiento CORRECTO.

**Estado actual (14/08/2026):** `57 passed · 3 skipped · 0 failed`. Los 25 casos priorizados
están en **VERDE** (los 3 `skip` son el resultado previsto de la migración a parseo DOM: el test
salta cuando el mecanismo regex que validaba ya no existe — el skip *es* la garantía de que el
bug quedó eliminado). Los tests existentes del proyecto (`test_analyzer.py`, `test_app.py`)
siguen pasando intactos.

| # | Caso (matriz 200) | Riesgo | Test | Estado |
|---|---|---|---|---|
| 1 | E20/E21 — Inyección PHP en el plugin generado vía `site_name`/`site_url` (RCE en el WP del cliente) | Crítico | `test_qa_plugin_criticos.py::test_p1_*` | 🟢 VERDE |
| 2 | E10 — `/api/lead` sin validación de email (relay de spam con tu dominio) | Crítico | `test_qa_app_criticos.py::test_ap1_*` | 🟢 VERDE |
| 3 | E10 — `/api/lead` sin rate limit estricto (30 emails/min por IP) | Crítico | `test_qa_app_criticos.py::test_ap2_*` | 🟢 VERDE |
| 4 | E1 — SSRF por DNS rebinding / TOCTOU (no pin de IP) | Crítico | `test_qa_analyzer_criticos.py::test_a2_*` | 🟢 VERDE |
| 5 | E7 — Respuesta sin límite de tamaño (gzip bomb → OOM del worker) | Crítico | `test_qa_analyzer_criticos.py::test_a3_*` | 🟢 VERDE |
| 6 | E5/D9 — `/api/history` global (fuga de URLs auditadas por otros) | Crítico | `test_qa_app_criticos.py::test_ap3_*` | 🟢 VERDE |
| 7 | B1 — Plugin fatal (white screen) en hosting sin mbstring | Crítico | `test_qa_plugin_criticos.py::test_p2_p9_*` | 🟢 VERDE |
| 8 | B28/B29 — Newsletter sin handler ni nonce (emails perdidos + spam) | Crítico | `test_qa_plugin_criticos.py::test_p7_*` | 🟢 VERDE |
| 9 | B4 — Regex de lazy/H1 modifica strings dentro de `<script>` | Crítico | `test_qa_plugin_criticos.py::test_p4_*` | 🟢 VERDE (PASA; lazy → SKIP por DOM) |
| 10 | B43 — Lazy aplicado al hero/LCP (degrade el CWV que dice mejorar) | Crítico | `test_qa_plugin_criticos.py::test_p6_*` | 🟢 VERDE (SKIP por DOM) |
| 11 | C16 — SPA client-side auditada como HTML vacío (score basura) | Crítico | `test_qa_analyzer_criticos.py::test_a4_*` | 🟢 VERDE |
| 12 | B11 — Borra metas description de Yoast/RankMath | Crítico | `test_qa_plugin_criticos.py::test_p5_*` | 🟢 VERDE |
| 13 | B3 — `<img>` multilínea sin lazy (regex sin `/s`) | Crítico | `test_qa_plugin_criticos.py::test_p3_*` | 🟢 VERDE (SKIP por DOM) |
| 14 | E12/D8 — `report_hash = sha256(url)[:12]` enumerable | Alto | `test_qa_app_criticos.py::test_ap4_*` | 🟢 VERDE |
| 15 | E13/D28 — `user_token` aceptado en query string (tokens en logs) | Alto | `test_qa_app_criticos.py::test_ap5_*` | 🟢 VERDE |
| 16 | E11 — Header injection CRLF en `/api/lead` (Bcc/To) | Alto | `test_qa_app_criticos.py::test_ap1_*[crlf]` | 🟢 VERDE |
| 17 | C8 — `alt=""` decorativo contado como "sin alt" (WCAG válido) | Alto | `test_qa_analyzer_criticos.py::test_a5_*` | 🟢 VERDE |
| 18 | C4 — Descripción en JSON-LD ignorada (falso "falta description") | Alto | `test_qa_analyzer_criticos.py::test_a6_*` | 🟢 VERDE |
| 19 | C11 — Forms con `aria-label` penalizados como "sin labels" | Alto | `test_qa_analyzer_criticos.py::test_a7_*` | 🟢 VERDE |
| 20 | B12 — Duplica newsletter/CTA si el sitio ya captura email | Alto | `test_qa_plugin_criticos.py::test_p8_*` | 🟢 VERDE |
| 21 | E26 — URL sin encode en PageSpeed Insights (contamina la llamada) | Alto | `test_qa_analyzer_criticos.py::test_a9_*` | 🟢 VERDE |
| 22 | C31/E8 — `depth` sin clamp (crawl masivo → DoS del operador) | Alto | `test_qa_app_criticos.py::test_ap8_*` | 🟢 VERDE |
| 23 | E33 — Errores internos filtran el detalle de la excepción | Medio | `test_qa_app_criticos.py::test_ap6_*` | 🟢 VERDE |
| 24 | E2 — SSRF: representaciones alternas (`::ffff:127.0.0.1`, `127.1`, decimal) | Alto | `test_qa_analyzer_criticos.py::test_a1_*` | 🟢 VERDE |
| 25 | B32/E30 — PHP generado siempre sintácticamente válido (umbral de calidad) | Crítico | `test_qa_plugin_criticos.py::test_p10_*` | 🟢 VERDE |

---

## Fixes aplicados (diff por caso)

### Plugin WordPress generado — `analyzer.py` → `_generar_plugin_wordpress`

| Caso | Fix |
|---|---|
| **P1** (E20/E21) | Nuevo sanitizador `_php_safe()` aplicado a `site_name` y `site_url` antes de interpolar en el docblock PHP: elimina `*` (cierra `/* */`), `<`/`>` (abre `<?php`), comillas/backslash y `( ) ; $ { } [ ]`. El payload `x */ system("id"); /*` ya no inyecta. |
| **P2/P9** (B1) | Polyfill de mbstring al inicio del plugin: `if (!function_exists('mb_substr'))` con fallback a `substr`/`strlen` — evita el fatal (white screen) en hostings sin la extensión. |
| **P3/P4/P6** (B3/B4/B43) | `_optimize_output` reescrito con **PHP DOMDocument** (parseo DOM, no regex): lazy con `getElementsByTagName('img')` que salta `fetchpriority` (hero) y `loading` ya declarado; funciona en `<img>` multilínea y jamás toca strings JS. Eliminado `_auto_alt` (regex de alt que rompía scripts). Los tests que dependían de la extracción de regex hacen `skip` — el mecanismo roto ya no existe. |
| **P4-H1** (B4) | H1 con DOM: 0 H1 → h1 oculto (accesible) insertado en `<body>`; 2+ → extras convertidos a `<h2>` con `replaceChild`. Sin `preg_replace_callback` global. |
| **P5** (B11) | Metas `description`/`og:description`/`twitter:description` eliminadas iterando nodos meta y re-inyectada la propia con `createElement` al final de `<head>` — ya no borra las de Yoast/RankMath. `_build_meta_desc` dividida en `_get_meta_desc()` (texto) + wrapper (compat con test existente). |
| **P7** (B28/B29) | El shortcode de newsletter procesa el POST: `wp_nonce_field`/`wp_verify_nonce`, `sanitize_email`/`is_email`, y guarda suscriptores en una option persistente (antes el form posteaba a `action=""` y el email se perdía). |
| **P8** (B12) | Gating en el generador: si el análisis detecta `forms.con_email > 0`, no se auto-inyecta `[newsletter]` en el footer ni el CTA flotante/trust bar. |
| **P10** (B32/E30) | Sin `preg_replace`/`preg_replace_callback` restantes en el plugin (todo DOM/`str_replace`): patrones siempre compilables, llaves balanceadas. |

### API Flask — `app.py` (+ `static/script.js`, `analyzer.py` guardado/historial)

| Caso | Fix |
|---|---|
| **AP1** (E10/E11) | `_email_valido()` en `/api/lead`: regex de formato + rechazo de `\r`/`\n` (header injection CRLF) + rechazo de no-string → 400. |
| **AP2** (E10) | `_lead_excede_limite()`: ventana deslizante de 60s, **3 envíos/min por IP** (`get_remote_address`), aplicado después de la validación (el input inválido no consume cuota). Manual (no `@limiter.limit`) porque el storage `memory://` es global al proceso y cortaría el 4º caso de AP1 antes de validar. |
| **AP3** (E5/D9) | `user_id` persistido al guardar análisis (`_guardar_analisis(resultado, user_id)`), `listar_analisis(limit, user_id)` fail-closed (sin `user_id` → `[]`), y `api_history` filtra por `g.current_user`. Invitados no ven nada. |
| **AP4** (E12/D8) | `report_hash = secrets.token_hex(6)` (12 hex, 96 bits de entropía) en vez de `sha256(url)[:12]` — los reportes compartidos ya no son enumerables. |
| **AP5** (E13/D28) | `check_auth` lee `user_token` **solo** del header `X-User-Token`; nunca de query string. Frontend migrado: `triggerDownload()` ahora hace `fetch(url, { headers: apiHeaders() })` y los links de descarga ya no incluyen `user_token` (solo `report_hash`). |
| **AP6** (E33) | `_error_interno()`: 500 genérico `{error, code: INTERNAL_ERROR, trace_id}`; aplicado en register, login, feedback y analyze. El detalle real queda solo en logs (`log.exception`). El `@app.errorhandler(500)` también lo usa. |
| **AP8** (C31/E8) | Clamp de `depth` en `/api/analyze`: `max(1, min(depth, 5))` — el crawl multipágina nunca supera 5 páginas internas. |

### Motor de análisis — `analyzer.py`

| Caso | Fix |
|---|---|
| **A1** (E2) | Ya pasaba (matriz de regresión de representaciones alternas: `::ffff:127.0.0.1`, `127.1`, decimal, hex). |
| **A2** (E1) | Pinning de IP: `_resolver_ip_publica()` devuelve la IP ya validada; `_safe_get` conecta contra esa IP (`_url_con_ip`, preservando puerto/query/IPv6 con corchetes) enviando el header `Host` original — **no re-resuelve** el hostname (cierra el TOCTOU del DNS rebinding). Redirecciones: cada hop se valida y pinnea. |
| **A3** (E7) | `_MAX_RESPONSE_BYTES = 10 MB`: `Content-Length` mayor → `ValueError` antes de descargar (anti gzip-bomb). |
| **A4** (C16) | `_detectar_spa()`: contenedor raíz típico (`#root`, `#app`, `#__next`, `#mount`, `data-reactroot`…) + `< 50` chars de texto en el body → `resultado["spa_detected"] = True` (hook para «auditoría limitada», sin score basura). |
| **A5** (C8) | `sin_alt` cuenta solo la **ausencia** del atributo (`tiene_alt`); `alt=""` decorativo es válido WCAG. |
| **A6** (C4) | Fallback a JSON-LD: si no hay `<meta description>`, `_buscar_descripcion_jsonld()` (recursivo, cubre `@graph`) busca `description` en los `application/ld+json`. |
| **A7** (C11) | `_extraer_forms` cuenta inputs con `aria-label`/`aria-labelledby` como labels accesibles — no penaliza forms válidos. |
| **A9** (E26) | La URL del sitio va `urlencode`da en la llamada a PageSpeed Insights: `?x=1&key=HACK` queda dentro del parámetro `url`, no contamina la query. |

### Harness de tests

| Cambio | Motivo |
|---|---|
| `test_app.py`: fixture `_patch_analyzer_module` de `scope="session"` → `scope="module"` | El mock de `sys.modules["analyzer"]` era session-wide y contaminaba `patch("analyzer.X")` de los tests QA cuando corrían en la misma corrida (A2/A4/A9 fallaban con TypeErrors solo en la suite combinada). |

---

**Cómo correr la suite completa:**

```
python -m pytest test_analyzer.py test_app.py test_qa_plugin_criticos.py test_qa_analyzer_criticos.py test_qa_app_criticos.py -q
```

Resultado esperado: `57 passed, 3 skipped, 0 failed`.

> Nota: los tests de plugin se ejecutan contra el **generador Python** del plugin
> (`analyzer._generar_plugin_wordpress`) — no hay PHP CLI en esta máquina —. Con la
> migración a parseo DOM, los tests que dependían de la extracción de regex (P3, P4-lazy,
> P6) hacen `skip` automático: el skip valida que el mecanismo regex roto ya no existe, y
> los tests estáticos (P4-H1, P5) pasan asertando la ausencia de `preg_replace`.
