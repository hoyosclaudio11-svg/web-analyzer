# QA — Siguiente tanda: casos sin test priorizados (operación, datos y robustez)

Después de los 25 críticos ya corregidos (`QA-25-priorizados-y-tests.md`, suite `57 passed ·
3 skipped · 0 failed`), quedan **169 casos de la matriz de 200 sin test** (11 Críticos, 45 Altos,
55 Medios, 58 Bajos). De los 11 Críticos restantes, `A4` (SPA) ya está cubierto por `test_a4`
(la matriz tiene `A4` y `C16` como casos distintos de SPA; el test cubre ambos comportamientos
con el flag `spa_detected`), así que quedan **10 Críticos accionables**.

Esta tanda prioriza por **probabilidad × impacto**, con foco en las cuatro áreas operativas
pedidas: **purga de `analisis/`, consentimiento de datos de terceros, saneamiento/rotación de
logs y TTL de reportes** — más los Críticos restantes que comparten la misma naturaleza
(datos, reportes y robustez del plugin).

## Ranking de la siguiente tanda

| # | Caso (matriz) | Área | Severidad | Prob × Impacto | Test sugerido |
|---|---|---|---|---|---|
| 1 | **D5** — Email de lead con link roto (`/report/` vs `/r/`) | TTL/entrega de reportes | Crítico | ★★★★★ — el 100% de los leads con `report_hash` recibe un link inaccesible | Assert en `api_lead`: `report_url` usa `/r/{hash}` (o se genera del router) |
| 2 | **E9** — Disk fill: `_guardar_analisis` sin rotación/purga | Purga de `analisis/` | Alto | ★★★★☆ — cualquier uso normal acumula JSON por corrida → disco lleno | Purga por TTL (antigüedad) + límite de archivos por dominio |
| 3 | **D10** — Datos de sitios de terceros guardados sin consentimiento ni TTL | Consentimiento + TTL | Alto | ★★★★☆ — retención indefinida de `meta`/`forms`/`imagenes`/`enlaces` (legal) | TTL en `analisis/`; excluir valores de inputs; disclaimer en política |
| 4 | **D19** — Plugin WordPress generado para sitios Wix/Squarespace | Robustez del plugin | Crítico | ★★★★☆ — cualquier sitio no-WP recibe un ZIP inútil | `_generar_soluciones` solo ofrece el plugin si se detectó WordPress |
| 5 | **D1** — CTA/trust bar de marca sobre sitios sensibles (salud/legal/financiero) | Reputación/legal | Crítico | ★★★★☆ — branding del SaaS en el sitio del cliente sin pedirlo | Gating del CTA por rubro detectado; toggle de marca OFF por defecto |
| 6 | **D21** — Newsletter del plugin sin consentimiento ni política (Ley 25.326/GDPR) | Consentimiento | Alto | ★★★★☆ — todo form del plugin queda ilegal para clientes UE/AR | Checkbox requerido + link a política en el form generado |
| 7 | **A3** — WAF/anti-bot (Cloudflare challenge) auditado como sitio real | Falsos diagnósticos | Crítico | ★★★☆☆ — sitios detrás de challenge reciben score basura | Detectar challenge/403 y devolver «sitio protegido por WAF» |
| 8 | **A15** — `<h1>` dentro de `<svg>`/`<template>`/JS contado como H1 real | Falsos diagnósticos | Crítico | ★★★☆☆ — conteo de H1 falso (el plugin ya no reescribe con regex; el *análisis* sí cuenta mal) | `_extraer_headings` ignora svg/template/script |
| 9 | **A6** — Sitio multiidioma (WPML/Polylang): metas por idioma pisadas | Falsos diagnósticos | Crítico | ★★★☆☆ — el plugin ya no borra metas (P5), el *análisis* debe respetar hreflang | No marcar «falta description» si hay metas por idioma + hreflang |
| 10 | **B25/B19** — `defer` agregado a scripts que usan `document.write` (chat/CRM: Tawk.to, Crisp, HubSpot) | Robustez del plugin | Crítico | ★★★☆☆ — widgets de terceros rotos en el sitio del cliente | Excluir del `defer` los scripts de chat/CRM y los que usan `document.write` |
| 11 | **E13** — Tokens en logs de acceso/proxy | Saneamiento de logs | Alto | ★★★☆☆ — ya se quitó el query-string (AP5); falta sanitizar logs | Assert: el log no contiene el token (log estructurado sin headers) |
| 12 | **C13** — Contraste de colores bajo NO medido (falso 9/10 en Accesibilidad) | Falsos diagnósticos | Crítico | ★★★☆☆ — riesgo WCAG/legal; requiere medir contraste | Cálculo de ratio de contraste sobre colores detectados |
| 13 | **D6** — Email sin `report_hash` apunta al sitio del cliente | TTL/entrega de reportes | Medio | ★★☆☆☆ — confusión, pero ya se genera hash en el flujo normal | Generar `report_hash` server-side siempre |
| 14 | **E31** — Log injection (CRLF en la URL entra al log) | Saneamiento de logs | Bajo | ★★☆☆☆ — `log.info(f"url={url}")` sin escapar CRLF | Sanear/escapar CRLF en logs |
| 15 | **E14** — Tokens de sesión sin expiración/rotación en logout | TTL de sesiones | Medio | ★★☆☆☆ — sesión persistente tras logout | Logout que borre/rote el token; TTL razonable |

## Detalle por área pedida

### 1. Purga de `analisis/` (E9, D10)
Hoy `_guardar_analisis` escribe un JSON por corrida con nombre `{dominio}_{timestamp}.json`, sin
rotación ni purga. Un uso normal del SaaS acumula archivos hasta llenar el disco (E9) y retiene
datos de sitios de terceros indefinidamente (D10).
**Fix mínimo:** purga por antigüedad (TTL, p. ej. 30 días) al guardar + tope de archivos por
dominio (p. ej. 20). **Test:** crear N archivos viejos → el guardado nuevo los purga; un dominio
con +N análisis conserva solo los últimos.

### 2. Consentimiento de datos de terceros (D10, D21)
El JSON de análisis guarda `meta`, `forms`, `imagenes`, `enlaces` del sitio ajeno sin
consentimiento ni política (D10); el form de newsletter del plugin no pide consentimiento ni
muestra política (D21, Ley 25.326/GDPR).
**Fix mínimo:** disclaimer en la política de privacidad + excluir valores de inputs del JSON;
checkbox de consentimiento + link a política en el form del plugin.
**Test:** el JSON guardado no contiene valores de inputs; el form generado incluye checkbox.

### 3. Saneamiento/rotación de logs (E31, E13)
`log.info(f"url={url}")` interpola la URL cruda: un `\n` forjado inyecta líneas falsas (E31);
los tokens de sesión aparecen en logs de acceso/proxy (E13 — el vector principal ya se cerró con
AP5, falta el saneamiento residual).
**Fix mínimo:** escapar CRLF en lo que se loguea; no loguear headers de auth; log estructurado.
**Test:** URL con `\nInjected` → el log no contiene la línea falsa; el log de un request
autenticado no contiene el token.

### 4. TTL de reportes (D5, D6, E14)
El email de lead arma `https://webanalyzer.com.ar/report/{hash}` pero la ruta real es
`/r/{hash}` (D5 — Crítico, link siempre roto); sin `report_hash` el email apunta al sitio del
cliente (D6); y los tokens de sesión no rotan en logout (E14).
**Fix mínimo:** usar `/r/` (o generar el link del router); generar `report_hash` server-side
siempre; logout que invalide/rote el token.
**Test (D5, ya listo para escribir):** POST a `/api/lead` con `report_hash` → el `report_url`
de la respuesta/email usa `/r/`.

## Notas de consistencia de la matriz

- **A4 vs C16:** ambos son SPA client-side en la matriz (A4 en la sección A, C16 en la C). El
  `test_a4` cubre ambos (flag `spa_detected`); en el QA-25 figura como C16. No duplicar tests.
- **E8 vs C31 y E2 vs A1:** pares equivalentes ya cubiertos (AP8 y A1 respectivamente).
- **D9/AP3 y D28/AP5:** ya cubiertos; E13 y E31 son el residuo de logs de esos mismos flujos.

**Cómo seguir:** escribir los tests de la fila 1 (D5) y 2-3 (E9/D10) primero — son los de mayor
prob×impacto y no requieren features nuevas (solo asserts y una purga simple). El resto de la
tanda (A3, A15, A6, B25, C13) son del motor/plugin y van después.
