# Baseline pasiva del endpoint de WebAnalyzer

**Fecha:** 2026-10-22
**Destino:** `https://web-analyzer-1-l8uc.onrender.com/`
**Método:** una solicitud GET normal, con el User-Agent identificable de WebAnalyzer. No se usó PageSpeed, no se enviaron payloads ni se enumeraron rutas; no se persistió el resultado.

Con el catálogo `argon-security-controls-v2`, la solicitud al endpoint respondió y el analizador local produjo estos datos:

- Puntaje pasivo: **2,3/10**.
- Cobertura: **7/22 controles**; 1 correcto, 6 observaciones, 12 no evaluados y 3 controles de cookies no aplicables.
- Observaciones de cabeceras: HSTS, CSP, nosniff, protección contra marcos, Referrer-Policy y Permissions-Policy.

Este es un punto de comparación del servicio público, no una auditoría completa. La fuente local de Flask configura CSP, nosniff, protección contra marcos y Referrer-Policy, y esta etapa añade HSTS y Permissions-Policy. La diferencia observada debe contrastarse en staging para confirmar qué revisión de código atiende actualmente Render.

Después del despliegue de staging, repetir esta misma comprobación pasiva y comparar cabeceras y versión del motor. Mantener la bandera de seguridad desactivada en producción hasta aprobar esa comparación.

## Arquitectura del despliegue actual

- `web-analyzer-1-l8uc.onrender.com` responde 200 en `/` y `/api/health`, pero las respuestas observadas no incluyen HSTS ni CSP.
- `webanalyzer.com.ar` sirve un proyecto Next.js en Vercel; su respuesta incluye HSTS, pero no CSP.
- La inspección de Vercel mostró `gitSource: null`. El repositorio local y los repositorios accesibles de GitHub contienen el backend Flask, pero no el código fuente Next.js de ese proyecto.
- El bundle público del formulario principal envía `POST /api/audits` al mismo dominio con `{url}` y espera un `id`. Este backend Flask expone `POST /api/analyze`; no se pudo inspeccionar la implementación de `/api/audits` para confirmar si hoy reenvía al servicio Flask.
- Por eso, desplegar este branch solo actualizaría el backend Flask. La integración visible en el dominio principal requiere localizar el código Next.js y verificar cómo conecta hoy con el backend.
