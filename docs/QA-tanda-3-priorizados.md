# QA — Tanda 3: barrido de severidad Media/Baja (próximos 10 priorizados)

Después de los 25 críticos (`QA-25-priorizados-y-tests.md`), la tanda operativa 1–15
(`QA-siguientes-priorizados.md`), la tanda 2 de 10 (`QA-tanda-2-priorizados.md`) y las
reservas E35/E29/E16/C15, la suite está en **97 passed · 3 skipped · 0 failed**.

Quedan **~157 casos de la matriz de 200 sin test** (45 Altos, 45 Medios, 56 Bajos y 11
Críticos — la mayoría de los Críticos son cross-refs ya cubiertos: E20/E21=P1, D9=AP3,
E10=AP2, B1=P2, E8=AP8, E12=AP4). Esta tanda prioriza los próximos 10 por
**probabilidad × impacto**, verificando cada candidato contra el código real.

## Ranking — tanda 3 (verificación en código real)

| # | Caso (matriz) | Severidad | Verificación en el código | Estado | Test sugerido |
|---|---|---|---|---|---|
| 1 | **A35** — credenciales en la URL (`https://user:pass@host`) | Alto | 🔴 **REAL:** `analizar` guarda `resultado["url"]=url` crudo; `_url_con_ip` preserva `parsed.username` en el netloc → la password viaja al fetch, se persiste en `analisis/`, entra al email del lead y al `site_url` del plugin. `_sanear_log` no la quita | Fix | `analizar("https://user:pass@x.com")` → `resultado["url"]`, `url_final` y logs sin la password |
| 2 | **A22** — HTTP 200 con página de error («database connection lost») | Alto | 🔴 **REAL:** el motor solo detecta WAF/anti-bot (`_detectar_waf`); una página de error en 200 se audita como sitio real → scorecard basura de 1/10 | Fix | 200 con marcadores de error → aviso claro en `errores`, sin scorecard |
| 3 | **B29** — spam en el form del newsletter del plugin | Alto | 🔴 **REAL:** el form tiene nonce + consent (D21) pero **sin honeypot** → un bot con el nonce válido guarda emails ilimitados en `wp_options` | Fix | ZIP contiene honeypot oculto; el handler ignora el POST si el honeypot viene lleno |
| 4 | **D16** — ZIP con nombre por dominio (multitienda) | Alto | 🔴 **REAL:** `_generar_soluciones` nombra `{safe_domain}_optimizer.zip` y `_guardar_analisis` lo escribe a `output/` por ese nombre → dos análisis del mismo dominio **se pisan** (el 2º sobrescribe el 1º) | Fix | dos `analizar()` del mismo dominio → nombres de ZIP distintos, ambos persisten |
| 5 | **C18** — no-determinismo entre análisis | Alto | 🟢 **DETERMINÍSTICO** (verificado: 2 corridas con el mismo fetch → scorecard idéntico; solo `fecha` difiere, por diseño) → **lock de regresión** | Lock | dos `analizar()` iguales → scorecard idéntico |
| 6 | **E3** — SSRF por redirect a host interno | Alto | 🟢 **YA MITIGADO:** `_safe_get` sigue redirects manualmente y revalida cada salto con `_resolver_ip_publica` → un `Location: http://127.0.0.1/` se bloquea en el hop → **lock** | Lock | 302 a loopback → `ValueError` «URL bloqueada» |
| 7 | **D28** — `X-User-Token` por query string | Alto | 🟢 **YA MITIGADO:** el frontend usa solo header (`script.js:22,227`); el backend rechaza query (AP5) → **lock estático** | Lock | `script.js` sin `user_token=` en query de fetch |
| 8 | **B12** — doble newsletter si el sitio ya tiene form | Alto | 🟢 **YA MITIGADO:** `con_email > 0 → sin newsletter_footer ni CTA` (líneas 1203-1219) → **lock** | Lock | sitio con form de email → plugin sin `[newsletter]` en `wp_footer` |
| 9 | **A20** — search/login form con campo email | Alto | 🟢 **Comportamiento correcto:** cualquier form con input email cuenta `con_email` → el plugin no agrega newsletter → **lock** | Lock | form de login con email → plugin sin `newsletter_footer` |
| 10 | **E5** — protocolos no-HTTP (`file://`, `gopher://`, `dict://`, `ftp://`) | Alto | 🟢 **YA CUBIERTO en parte** (`file:///etc/passwd` en `test_analyzer.py:41`; `_resolver_ip_publica` exige http/https) → **lock extendido** | Lock | parametrizado gopher/dict/ftp → bloqueados |

## Hallazgos del barrido

- **4 fixes reales** (A35, A22, B29, D16) y **1 lock funcional** (C18) sobre el motor; el
  resto son **locks de regresión** sobre código ya blindado (E3, D28, B12, A20, E5).
- **A35 es el más grave de la tanda:** el userinfo no solo queda en el request (básica auth)
  sino que se persiste en `analisis/`, entra al email del lead y al `site_url` del plugin
  generado. Fix en dos puntos: `analizar` debe quitar userinfo al entrar (cubre DB/plugin/
  email) y `_sanear_log` debe quitar userinfo (cubre los logs de `api_analyze`).
- **A22** usa una lista acotada de marcadores (`database connection lost`, `error
  establishing a database connection`, `internal server error`, `500 internal server
  error`, `site under maintenance`) solo en respuestas 200, para evitar falsos positivos
  en páginas legítimas que contengan esas palabras.
- **D16:** el front descarga por `s.nombre` del response (no por un nombre fijo), así que
  un nombre único `{safe_domain}_optimizer_{secrets.token_hex(3)}.zip` se propaga solo.
  Requiere `import secrets` en `analyzer.py` (hoy no está).
- **B29:** el honeypot es un campo oculto (`position:absolute;left:-9999px`) que un humano
  nunca completa; si viene lleno, el handler responde éxito falso sin guardar.
- **C18 fue verificado empíricamente** (2 corridas idénticas → `scorecard` igual); la
  diferencia entre análisis está solo en `fecha` (timestamp, por diseño).
- **D25 (monitoreo sin scheduler) es un gap de producto real:** no hay cron/thread/scheduler
  en el código — `/api/monitor` guarda URLs pero nada re-ejecuta el análisis. No es un bug
  testeable sino una decisión de feature; queda documentado.

## Alternativas de reserva (próximo barrido)

- **E19** — XSS almacenado vía feedback: solo se renderiza en el modal del propio usuario
  (sin vista admin encontrada) → riesgo bajo, lock barato.
- **C1** — B2B corporativo sin newsletter: el gating actual es por rubro sensible (D1), no
  por tipo de negocio → decisión de producto, no bug.
- **D25** — monitoreo sin scheduler visible: documentar el alcance o agregar un worker.
- **B7** — entidades en title (`Foo &amp; Bar`): BeautifulSoup las decodifica en
  `soup.title.string` → verificar con lock.
- **B44** — lazy sin `width`/`height` (CLS): documentar en el plugin.
- **E37** — form del newsletter sin handler visible: el handler real guarda en
  `wp_options` con nonce + consent (B29 lo endurece) → riesgo bajo.

**Cómo seguir:** arrancar por las filas 1–4 (A35, A22, B29, D16) — bugs confirmados con
fixes de pocas líneas y tests directos — y cerrar con los locks 5–10 (C18 funcional + 5
estáticos/de comportamiento). Tras esta tanda quedarían ~147 casos de la matriz sin test.
