# QA — Siguiente tanda: casos sin test priorizados (operación, datos y robustez)

Después de los 25 críticos ya corregidos (`QA-25-priorizados-y-tests.md`), quedaban **169
casos de la matriz de 200 sin test** (11 Críticos, 45 Altos, 55 Medios, 58 Bajos). De los 11
Críticos restantes, `A4` (SPA) ya estaba cubierto por `test_a4` (la matriz tiene `A4` y `C16`
como casos distintos de SPA; el test cubre ambos comportamientos con el flag `spa_detected`),
así que quedaron **10 Críticos accionables**.

Esta tanda priorizó por **probabilidad × impacto**, con foco en las cuatro áreas operativas
pedidas: **purga de `analisis/`, consentimiento de datos de terceros, saneamiento/rotación de
logs y TTL de reportes** — más los Críticos restantes que comparten la misma naturaleza
(datos, reportes y robustez del plugin).

**Estado actual (14/08/2026):** las 15 filas del ranking están en **VERDE** — `79 passed ·
3 skipped · 0 failed` en la suite completa (6 archivos). Cada fila se cerró con tests en rojo
→ fix → verde, en 4 commits.

## Ranking de la siguiente tanda

| # | Caso (matriz) | Área | Severidad | Prob × Impacto | Estado |
|---|---|---|---|---|---|
| 1 | **D5** — Email de lead con link roto (`/report/` vs `/r/`) | TTL/entrega de reportes | Crítico | ★★★★★ | 🟢 VERDE |
| 2 | **E9** — Disk fill: `_guardar_analisis` sin rotación/purga | Purga de `analisis/` | Alto | ★★★★☆ | 🟢 VERDE |
| 3 | **D10** — Datos de sitios de terceros guardados sin consentimiento ni TTL | Consentimiento + TTL | Alto | ★★★★☆ | 🟢 VERDE |
| 4 | **D19** — Plugin WordPress generado para sitios Wix/Squarespace | Robustez del plugin | Crítico | ★★★★☆ | 🟢 VERDE |
| 5 | **D1** — CTA/trust bar de marca sobre sitios sensibles (salud/legal/financiero) | Reputación/legal | Crítico | ★★★★☆ | 🟢 VERDE |
| 6 | **D21** — Newsletter del plugin sin consentimiento ni política (Ley 25.326/GDPR) | Consentimiento | Alto | ★★★★☆ | 🟢 VERDE |
| 7 | **A3** — WAF/anti-bot (Cloudflare challenge) auditado como sitio real | Falsos diagnósticos | Crítico | ★★★☆☆ | 🟢 VERDE |
| 8 | **A15** — `<h1>` dentro de `<svg>`/`<template>`/JS contado como H1 real | Falsos diagnósticos | Crítico | ★★★☆☆ | 🟢 VERDE |
| 9 | **A6** — Sitio multiidioma (WPML/Polylang): metas por idioma pisadas | Falsos diagnósticos | Crítico | ★★★☆☆ | 🟢 VERDE |
| 10 | **B25/B19** — `defer` agregado a scripts que usan `document.write` (chat/CRM) | Robustez del plugin | Crítico | ★★★☆☆ | 🟢 VERDE |
| 11 | **E13** — Tokens en logs de acceso/proxy | Saneamiento de logs | Alto | ★★★☆☆ | 🟢 VERDE |
| 12 | **C13** — Contraste de colores bajo NO medido (falso 9/10 en Accesibilidad) | Falsos diagnósticos | Crítico | ★★★☆☆ | 🟢 VERDE |
| 13 | **D6** — Email sin `report_hash` apunta al sitio del cliente | TTL/entrega de reportes | Medio | ★★☆☆☆ | 🟢 VERDE |
| 14 | **E31** — Log injection (CRLF en la URL entra al log) | Saneamiento de logs | Bajo | ★★☆☆☆ | 🟢 VERDE |
| 15 | **E14** — Tokens de sesión sin expiración/rotación en logout | TTL de sesiones | Medio | ★★☆☆☆ | 🟢 VERDE |

## Fixes aplicados (diff por caso)

### Tanda 1–3 — operación y retención (`commit 2ba0d09`)

| Caso | Fix | Test |
|---|---|---|
| **D5** | `app.py` — `report_url = f"https://webanalyzer.com.ar/r/{report_hash}"` (ruta real, antes `/report/`) | `test_d5_email_lead_usa_ruta_real_del_reporte` |
| **E9** | `analyzer.py` — `_purga_analisis()` al inicio de `_guardar_analisis`: borra `.json` con más de 30 días y conserva los 20 más recientes por dominio | `test_e9_guardar_analisis_purga_por_antiguedad`, `test_e9_tope_de_archivos_por_dominio` |
| **D10** | `analyzer.py` — `_sin_valores_sensibles()`: filtra recursivamente `value`/`valores`/`password`/`secret`/`token`/`api_key` antes de persistir | `test_d10_json_guardado_excluye_valores_de_inputs` |

### Tanda 4–6 — plugin y consentimiento (`commit 55261e2`)

| Caso | Fix | Test |
|---|---|---|
| **D19** | `analyzer.py` — el ZIP del plugin solo se genera si `tech` contiene WordPress (`es_wordpress = any("WordPress" in t for t in tech)`) | `test_d19_plugin_wordpress_solo_si_hay_wordpress` |
| **D1** | `analyzer.py` — `_rubro_sensible()` (salud/legal/financiero por keywords) omite el CTA flotante y la trust bar; erra hacia lo seguro | `test_d1_sitio_sensible_sin_cta_de_marca` |
| **D21** | `analyzer.py` — el handler del newsletter exige `_consent` (`isset`), form con checkbox `required` + link a `/privacidad` (Ley 25.326/GDPR) | `test_d21_newsletter_pide_consentimiento` |

### Tanda 7–10 — motor y plugin (`commit 8dff612`)

| Caso | Fix | Test |
|---|---|---|
| **A3** | `analyzer.py` — `_detectar_waf(resp)`: 403/429/503 con marcadores de challenge (Cloudflare/DataDome/Imperva) → `ValueError` claro antes de `raise_for_status`; `analizar` lo propaga a `errores` | `test_a3_waf_challenge_no_se_audita` (×3), `test_a3_waf_analizar_devuelve_error_claro` |
| **A15** | `analyzer.py` — `_extraer_headings` ignora tags con ancestro `script/style/template/noscript/svg` | `test_a15_headings_ignoran_svg_template_script` |
| **A6** | `analyzer.py` (plugin) — el bloque 5a ya no borra las meta description existentes (WPML/Polylang); inyecta la propia solo si `count($descripciones) === 0` | `test_a6_no_borra_metas_description_por_idioma` |
| **B25** | `analyzer.py` (plugin) — `_defer_scripts` excluye por handle **y** dominio: tawk, crisp, hubspot, intercom, zendesk, livechat, tidio (document.write) | `test_b25_defer_excluye_widgets_de_terceros` |

### Tanda 11–15 — logs, contraste y sesiones (`commit 81c352b`)

| Caso | Fix | Test |
|---|---|---|
| **C13** | `analyzer.py` — `_hex_a_rgb`/`_luminancia_relativa`/`_ratio_contraste`/`_medir_contraste`: ratio < 4.5:1 en estilos inline → −2 puntos + detalle WCAG | `test_c13_contraste_bajo_se_penaliza`, `test_c13_contraste_alto_no_se_penaliza` |
| **D6** | `app.py` — sin `report_hash`, `api_lead` genera `secrets.token_hex(6)` y persiste con `create_shared_report`; el link nunca apunta al sitio del cliente | `test_d6_email_lead_siempre_con_report_hash` |
| **E13** | Lock de regresión — el token (header o query) nunca aparece en logs (AP5 cerró el vector; este test lo garantiza) | `test_e13_token_no_aparece_en_logs` |
| **E31** | `app.py` — `_sanear_log()` escapa CR/LF; aplicado en `log_request` (path) y en los sitios de `url=` de `api_analyze`/`api_lead` | `test_e31_sanear_log_escapa_crlf`, `test_e31_crlf_en_path_no_inyecta_lineas`, `test_e31_crlf_en_url_no_inyecta_lineas` |
| **E14** | `database.py` — `revocar_token(token)` (`token`/`token_expires` → NULL) · `app.py` — nuevo `POST /api/auth/logout`; test real contra DB SQLite temporal | `test_e14_logout_revoca_el_token` |

## Historial de commits

```
81c352b Fix: contraste WCAG, saneamiento de logs, hash de lead y logout (fila 11-15)
8dff612 Fix: WAF/anti-bot, conteo de H1, metas por idioma y defer de widgets (fila 7-10)
55261e2 Fix: plugin solo para WordPress, sin branding en rubros sensibles y consentimiento en el newsletter
2ba0d09 Fix: retención y entrega de datos — link de reporte /r/, purga de analisis/ y valores de inputs
a1fee28 Fix: blindar plugin generado, API y motor de análisis (25 tests QA en verde)
```

## Detalle por área pedida

### 1. Purga de `analisis/` (E9, D10) — ✅ resuelto en `2ba0d09`
`_guardar_analisis` escribía un JSON por corrida sin rotación. Ahora `_purga_analisis()` corre al
guardar: TTL de 30 días + tope de 20 archivos por dominio; y `_sin_valores_sensibles()` excluye
valores de inputs/passwords del JSON persistido.

### 2. Consentimiento de datos de terceros (D10, D21) — ✅ resuelto en `2ba0d09` y `55261e2`
D10: los valores de inputs ya no se guardan en el JSON de análisis. D21: el form del newsletter
pide consentimiento (checkbox requerido) y referencia la política de privacidad.

### 3. Saneamiento/rotación de logs (E31, E13) — ✅ resuelto en `81c352b`
`_sanear_log()` escapa CR/LF en todo lo que se loguea desde entradas de usuario (URLs, paths);
los headers de auth nunca se loguean (E13 queda garantizado por test de regresión).

### 4. TTL de reportes (D5, D6, E14) — ✅ resuelto en `2ba0d09` y `81c352b`
D5: el email usa la ruta real `/r/{hash}`. D6: sin `report_hash` el server lo genera y persiste.
E14: logout revoca el token (TTL de 30 días ya existía en `get_user_by_token`).

## Notas de consistencia de la matriz

- **A4 vs C16:** ambos son SPA client-side en la matriz (A4 en la sección A, C16 en la C). El
  `test_a4` cubre ambos (flag `spa_detected`); en el QA-25 figura como C16. No duplicar tests.
- **E8 vs C31 y E2 vs A1:** pares equivalentes ya cubiertos (AP8 y A1 respectivamente).
- **D9/AP3 y D28/AP5:** ya cubiertos; E13 y E31 eran el residuo de logs de esos mismos flujos
  (cerrado en la fila 11–15).

**Cómo seguir:** de la matriz de 200 quedan ~149 casos de severidad Media/Baja sin test. El
próximo barrido debería rankearlos por probabilidad × impacto igual que esta tanda, con foco
en los que comparten naturaleza operativa (D7 email inválido, E15 lockout por cuenta, E16
registro sin verificación, A30/A31 hallazgos ya detectados).
