# QA — Tanda 2: barrido de severidad Media/Baja (10 priorizados — TODOS EN VERDE)

Después de los 25 críticos (`QA-25-priorizados-y-tests.md`) y la tanda operativa 1–15
(`QA-siguientes-priorizados.md`, suite `79 passed · 3 skipped · 0 failed`), quedaban **154
casos de la matriz de 200 sin test**: 42 Altos, 53 Medios, 57 Bajos y **2 Críticos** (B19 y
E39).

Esta tanda priorizó los próximos 10 por **probabilidad × impacto**, verificando cada candidato
contra el código real (no solo contra la descripción de la matriz). De los 10, **6 requirieron
fix**, **2 fueron hardening** y **2 fueron locks de regresión** sobre código ya blindado.

**Estado actual (14/08/2026):** las 10 filas del ranking están en **VERDE** — `91 passed ·
3 skipped · 0 failed` en la suite completa (6 archivos). Cada fila se cerró con tests en rojo
→ fix → verde, en 3 commits (`099af4a`, `fd04e97`, `0b066ab`).

## Ranking — tanda de 10

| # | Caso (matriz) | Severidad | Verificación en el código | Estado | Test que lo cierra |
|---|---|---|---|---|---|
| 1 | **E39** — `.env` con credenciales expuesto / SMTP password en el repo | Crítico | 🔴 → ✅ `app.py`: fallback `SMTP_PASS` hardcodeado eliminado (`""`), `send_email` falla cerrado sin credencial | 🟢 VERDE | `test_e39_smtp_pass_sin_fallback_hardcodeado` |
| 2 | **A40** — más de 10 redirects (loop) | Medio | 🔴 → ✅ `_safe_get`: respuesta final 3xx/`is_redirect` → `ValueError` «demasiados redirects», propagado a `errores` | 🟢 VERDE | `test_a40_loop_de_redirects_aborta` + `test_a40_analizar_reporta_loop_de_redirects` |
| 3 | **E22** — inyección PHP vía `safe_domain` (familia P1/P10) | Medio | 🔴 → ✅ `safe_domain` con dígito inicial se prefija con `w` → identificadores PHP válidos | 🟢 VERDE | `test_e22_safe_domain_con_digito_genera_php_valido` |
| 4 | **E15** — brute-force sin lockout por cuenta | Medio | 🟠 → ✅ `_LOGIN_FAILS` + helpers: 5 fallos/15 min → `429 ACCOUNT_LOCKED`, independiente de la IP | 🟢 VERDE | `test_e15_lockout_por_cuenta_independiente_de_ip` |
| 5 | **B19** — `defer` en script que un inline usa vía `document.write` | Crítico | 🟠 → ✅ `_generar_plugin_wordpress`: detección de `document.write` inline → bloque defer condicional (no emite `script_loader_tag`) | 🟢 VERDE | `test_b19_document_write_inline_desactiva_defer` |
| 6 | **A16** — hero con `loading="eager"` penalizado como «sin lazy» | Alto | 🔴 → ✅ `_extraer_imagenes`: `fetchpriority` en el dict, hero excluido de `sin_lazy` | 🟢 VERDE | `test_a16_hero_eager_no_penaliza_sin_lazy` (+ control `test_a16_img_sin_loading_sigue_contando_como_sin_lazy`) |
| 7 | **E40** — cabeceras de seguridad faltantes | Medio | 🔴 → ✅ `app.py`: `after_request security_headers` (nosniff, X-Frame-Options, Referrer-Policy, CSP) | 🟢 VERDE | `test_e40_cabeceras_de_seguridad` |
| 8 | **A31** — `meta robots noindex` en la página analizada | Medio | 🟠 → ✅ `_evaluar_seo`: `noindex` → score 10 informativo sin deducciones ni recomendaciones falsas | 🟢 VERDE | `test_a31_noindex_se_avisa_y_no_genera_recomendaciones_falsas` |
| 9 | **E18** — XSS reflejado vía datos del sitio analizado en el render | Alto | 🟢 Ya mitigado (`esc()` en `static/script.js`) → **lock de regresión** | 🟢 VERDE | `test_e18_render_escapa_datos_del_sitio` |
| 10 | **E25** — path traversal en `/api/download` | Medio | 🟢 Ya mitigado (regex + `basename` + `resolve` + prefijo) → **lock de regresión** | 🟢 VERDE | `test_e25_traversal_en_download_bloqueado` |

## Fixes aplicados (diff por caso)

### Tanda 2 — filas 1–3: credenciales, redirects y dominio PHP (`commit 099af4a`)

| Caso | Archivo | Diff del fix | Test |
|---|---|---|---|
| **E39** | `app.py` | `SMTP_PASS = os.environ.get("SMTP_PASS", "25YmQhbaWJ")` → fallback `""`; `send_email` devuelve `False` si no hay contraseña configurada («SMTP_PASS no configurado en el entorno») — la credencial quedó solo en `.env` (gitignored, no trackeado) | `test_e39_smtp_pass_sin_fallback_hardcodeado` |
| **A40** | `analyzer.py` | `_safe_get`: tras `break` por 10 hops, si `resp.is_redirect`/status 3xx → `ValueError("Demasiados redirects al acceder a {url} — se detuvo tras {hops} saltos")`; `analizar` lo propaga a `errores` (la 302 ya no se audita como sitio) | `test_a40_loop_de_redirects_aborta`, `test_a40_analizar_reporta_loop_de_redirects` |
| **E22** | `analyzer.py` | `safe_domain` con primer carácter dígito (o vacío) → se antepone `w` (`2do.com.ar` → `w2do_com_ar` → `function w2do_com_ar_cta_flotante()`); verificada la validez del ZIP real descomprimido | `test_e22_safe_domain_con_digito_genera_php_valido` |

### Tanda 2 — filas 4–6: lockout, defer y hero (`commit fd04e97`)

| Caso | Archivo | Diff del fix | Test |
|---|---|---|---|
| **E15** | `app.py` | Estado in-memory `_LOGIN_FAILS` (patrón de `_LEAD_SENDS`) con ventana deslizante: 5 fallos en 15 min → `429 ACCOUNT_LOCKED`, chequeado antes de `authenticate` y por **email normalizado** (`.lower()`), independiente de la IP; el login exitoso limpia los fallos | `test_e15_lockout_por_cuenta_independiente_de_ip` |
| **B19** | `analyzer.py` | `_generar_soluciones` detecta `document.write` en el HTML → `hay_document_write=True`; `_generar_plugin_wordpress` recibe el flag y el bloque defer pasa a ser `defer_block` condicional (no emite el filtro `script_loader_tag` cuando hay inline) | `test_b19_document_write_inline_desactiva_defer` |
| **A16** | `analyzer.py` | El dict de imágenes incluye `fetchpriority`; `sin_lazy` excluye imágenes con `loading="eager"` explícito o `fetchpriority="high"` (el hero no debe ser lazy). Control anti sobre-corrección: imagen sin `loading` sigue contando | `test_a16_hero_eager_no_penaliza_sin_lazy`, `test_a16_img_sin_loading_sigue_contando_como_sin_lazy` |

### Tanda 2 — filas 7–10: cabeceras, noindex y locks (`commit 0b066ab`)

| Caso | Archivo | Diff del fix | Test |
|---|---|---|---|
| **E40** | `app.py` | Nuevo `after_request security_headers` en toda respuesta: `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin` y CSP (`default-src 'self'`, script/style `'unsafe-inline'` por el JS inline del frontend, `frame-ancestors 'self'`) | `test_e40_cabeceras_de_seguridad` |
| **A31** | `analyzer.py` | `_evaluar_seo`: si `robots` declara `noindex` → score 10 con detalle «La página declara noindex — no debe indexarse; el score SEO es informativo», sin deducciones (antes puntuaba SEO normal con recomendaciones falsas de title/description) | `test_a31_noindex_se_avisa_y_no_genera_recomendaciones_falsas` |
| **E18** | `static/script.js` (lock) | Sin diff — ya blindado: `esc()` en todas las interpolaciones `${...}` de datos del sitio. Lock estático: 17 interpolaciones escapadas, 0 crudas; único no-escape legítimo `${h.impacto ? ...}` (ternario de truthiness) | `test_e18_render_escapa_datos_del_sitio` |
| **E25** | `app.py` (lock) | Sin diff — ya blindado: regex `^[a-zA-Z0-9_.\-]+$` + `basename` + `resolve` + prefijo. Lock: 7 variantes (`../../etc/passwd`, `%2f`, `%2e%2e`, `C:\Windows\win.ini`, UNC `\server\share`, `....//`, doble-encoding) → 400/403/404, nunca contenido | `test_e25_traversal_en_download_bloqueado` |

## Historial de commits (tanda 2)

```
0b066ab Fix: cabeceras de seguridad y aviso de noindex + locks de XSS y traversal (fila 7-10 tanda 2)
fd04e97 Fix: lockout por cuenta en login, sin defer con document.write inline y hero no penalizado (fila 4-6 tanda 2)
099af4a Fix: sin credencial SMTP hardcodeada, loop de redirects y safe_domain PHP válido (fila 1-3 tanda 2)
```

## Notas de implementación

- **E39** era el caso más grave de la tanda: la credencial `SMTP_PASS` de Ferozo estaba en el
  fuente commiteado. El test inspecciona el **source** de `app.py` (no el runtime, que por
  diseño depende del `.env` local). El path Resend (`RESEND_API_KEY`) sigue funcionando; el
  fallback SMTP solo falla cerrado si no hay credencial configurada.
- **Hallazgo de E18:** la primera versión del lock usaba un regex con bug de precedencia
  (`\$\{A|B|C` ancla el `${` solo a la primera alternativa) que daba falsos positivos; el
  patrón corregido usa grupo no-capturante. Este tipo de hallazgo valida el valor de los
  locks estáticos.
- **A40 y E22** eran bugs confirmados por lectura de código (la 302 final se auditaba como
  sitio; `safe_domain` generaba PHP inválido para dominios con dígito inicial — familia P10).
- **E15** testea con DB real en `tmp_path` y `limiter.reset()` para no chocar con el rate
  limit; el lockout es por email normalizado, así que un ataque distribuido no lo evade.

## Alternativas de reserva (siguiente barrido)

Siguen pendientes de la matriz (severidad media/baja, sin test):

- **E35** — IDOR en `DELETE /api/monitor?id=N`: ya filtrado (`delete_monitored_url(id, user_id)`); lock barato.
- **E29** — rate limit `memory://` se resetea en restart y no es multi-worker; migrar a storage persistente.
- **E16** — registro sin verificación de email (cuentas falsas abusan el tier free).
- **C14** — menú no operable por teclado: agregar disclaimer «auditoría limitada a lo estático» al reporte.
- **C15** — `<html>` sin atributo `lang`: chequeo barato de SEO/accesibilidad.
- **E19** — XSS almacenado vía feedback: el comentario solo se renderiza en el modal del propio usuario (sin vista admin encontrada) → riesgo bajo.

**Cómo seguir:** con la tanda 2 completa, quedan **~140 casos de severidad media/baja sin
test** de la matriz de 200. Candidatos naturales para el próximo barrido: las reservas E35
(lock), E29 (persistencia del rate limit), E16 (verificación de email) y C15 (`lang`), más
los casos Altos restantes del barrido original.
