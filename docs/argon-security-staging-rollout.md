# WebAnalyzer + Argon Defender: staging rollout

## Etapa actual

El backend entrega las auditorías ampliadas de Lighthouse y una matriz de cobertura para las 20 prácticas iniciales. El perfil pasivo de seguridad está detrás de `ARGON_SECURITY_ENABLED` y permanece apagado si la variable no existe o no vale `true`, `1`, `yes` u `on`.

## Alcance de esta rama

Esta rama actualiza el servicio Flask de Render. El dominio principal `webanalyzer.com.ar` usa un proyecto Next.js de Vercel separado; su formulario público llama a `POST /api/audits`, mientras que Flask expone `POST /api/analyze`. La inspección de producción mostró que el proyecto Vercel no está enlazado a un repositorio Git y su código no está en los repositorios locales disponibles. Falta revisar la implementación de `/api/audits` para saber si sirve de puente a Flask; no se debe atribuir a este despliegue un cambio visible en la interfaz Next.js hasta verificar e integrar ese flujo.

El catálogo versionado contiene 22 controles. Diez son observables en una respuesta HTTP normal: siete controles de transporte/cabeceras y tres atributos de cookies de sesión. Si la respuesta no emite una cookie de sesión reconocible, esos tres controles aparecen como `not_applicable`.

Los doce controles restantes reflejan familias que Argon Defender implementa o evalúa en su proxy, entre ellas firmas SQLi/XSS/inyección de comandos, políticas de rutas, límites de cuerpos y JSON, aislamiento de actores, señales TLS confiables y resiliencia del upstream. Se contrastaron con `src/proxy.py` y `src/cli.py` de Argon Defender. Una respuesta normal no permite verificar esos controles: aparecen como `not_evaluated`, no suman al puntaje y explican la cobertura. WebAnalyzer no ejecuta el CLI de Argon Defender ni sondea rutas o archivos del dominio analizado. Las pruebas activas quedan reservadas para una etapa posterior con verificación de dominio.

## Antes de desplegar staging

1. Preservar los cambios locales que ya existían en ambos repositorios con una copia verificable antes de preparar el branch de integración. Seleccionar los archivos del despliegue y comprobar el diff para no incluir esos cambios por accidente.
2. Crear el servicio desde `deploy/render-staging.yaml` en el branch `codex/argon-staging-20261023`, con un Blueprint separado del servicio `web-analyzer`. En Render, elegir esa ruta como Blueprint Path; la configuración usa `/api/health` como health check y despliega después de pasar GitHub Actions.
3. No configurar `DATABASE_URL` en staging: el backend usa SQLite dentro del propio servicio y nunca hereda la base de producción. Ese almacenamiento es efímero; para conservar reportes entre despliegues, conectar una base de datos de staging independiente.
4. Configurar `ARGON_SECURITY_ENABLED=true` solamente en staging. En producción, dejar la variable ausente o en `false` hasta completar la revisión. El Blueprint staging no administra ni modifica el servicio de producción.
5. En Render, configurar `TRUST_X_FORWARDED_FOR=true` solo porque las solicitudes llegan por su proxy confiable. El código valida la primera IP de `X-Forwarded-For`; fuera de ese entorno ignora ese encabezado por defecto. Render recomienda leer esa cabecera para obtener la IP real del cliente: https://render.com/articles/how-render-handles-ddos-attacks
6. Si staging usa varios workers o instancias, configurar un almacenamiento compartido para Flask-Limiter mediante `RATE_LIMIT_STORAGE_URI`; `memory://` limita por proceso.

## Verificación en staging

Ejecutar primero las pruebas locales del motor:

```powershell
python -m pytest test_security_audit.py test_practice_coverage.py test_security_rollout.py test_ssrf_hardening.py test_analyzer.py test_qa_analyzer_criticos.py test_app.py test_qa_app_criticos.py -q
python -m py_compile analyzer.py app.py security_audit.py practice_coverage.py
node --check static/script.js
```

Después, desde staging, analizar una página de un dominio controlado por el equipo y revisar:

- `versiones.motor` y `versiones.perfil_seguridad` en la respuesta.
- `seguridad.enabled == true` y la relación `seguridad.resumen.evaluados / catalogo_total` sobre los 22 controles versionados.
- Los doce controles `not_evaluated` que requieren evidencia activa o de servidor; no reducen el puntaje.
- Los controles `not_applicable` cuando la respuesta no emite cookies de sesión; no reducen el puntaje.
- `auditorias_rendimiento`, métricas CrUX disponibles y el desglose de cobertura de las 20 prácticas.
- El enlace `report_url`: debe mostrar el puntaje guardado y las versiones del motor y del catálogo.
- Un reporte anterior: sus valores persistidos deben seguir iguales después del despliegue.
- Los límites de cinco análisis por minuto por cuenta autenticada o por IP de invitado, además del límite general existente.
- El User-Agent identificable `WebAnalyzer/2.0 (+https://webanalyzer.com.ar/)` en las solicitudes del analizador y PageSpeed.
- Timeouts, máximo de diez redirecciones y corte del cuerpo al superar 10 MB descomprimidos, incluso si falta `Content-Length`.
- El acceso a `localhost`, redes privadas, rangos especiales/no globales y destinos de metadata debe continuar rechazado después de validar cada redirección y fijar la IP pública resuelta.

El nombre público del puntaje es **Índice Argon de seguridad web, basado en metodología Argon Defender**. El informe debe mostrar la cobertura efectiva; no presentar el valor como una garantía de que el sitio sea seguro en todos sus componentes.

## Reversión

Para quitar el nuevo puntaje sin cambiar código, establecer `ARGON_SECURITY_ENABLED=false` en staging y reiniciar el servicio. La categoría Seguridad deja de participar en nuevos promedios; los reportes ya guardados conservan sus valores y versiones. Si una versión de código falla, volver al despliegue anterior desde Render.

## Etapas posteriores

1. Activar producción solo después de verificar staging, respaldar los cambios locales y definir el rollback del servicio.
2. Incorporar pruebas activas de exposición únicamente después de verificar que el usuario controla el dominio, preferentemente mediante DNS TXT o mediante archivo/meta tag con token de un solo uso. Vincular la verificación al dominio exacto, con vencimiento y alcance visible en el informe.
   - Para la primera versión, priorizar un TXT aleatorio de un solo uso; validar el nombre exacto del dominio, guardar la verificación con fecha de vencimiento y no seguir redirecciones fuera del host verificado.
   - Ejecutar solo el conjunto explícito de pruebas de exposición aprobado para ese dominio, con límites de solicitudes y tamaño, timeouts y registro de la evidencia. No habilitar traversal ni cargas de payloads.
3. Mantener fuera del alcance inicial las búsquedas de `.env`, `.git`, backups, traversal y cualquier sondeo de rutas. La verificación habilitará una fase controlada futura; el CLI de Argon no recibe URLs de clientes.
4. Dejar el navegador automatizado y el conector de eventos de Argon Defender para la última etapa.
