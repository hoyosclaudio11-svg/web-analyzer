# Mapa del catálogo de seguridad Argon para WebAnalyzer

Este documento registra la relación entre evidencia HTTP observable por WebAnalyzer y familias defensivas de Argon Defender. WebAnalyzer no importa el proxy de Argon, no ejecuta su CLI y no convierte las pruebas internas de Argon en resultados del dominio analizado.

## Controles observables del perfil pasivo

Estos diez controles forman el denominador de la cobertura pasiva. Siete siempre se pueden medir con la respuesta inicial; los tres de cookies solo se evalúan cuando se observa una cookie de sesión reconocible.

| ID | Evidencia de WebAnalyzer | Estado si no aparece |
|---|---|---|
| `transport-https` | Esquema HTTPS de la URL final y conexión TLS verificada | Hallazgo |
| `header-hsts` | Cabecera Strict-Transport-Security en HTTPS | Hallazgo |
| `header-csp` | Presencia de Content-Security-Policy y heurística de política amplia | Hallazgo |
| `header-nosniff` | X-Content-Type-Options: nosniff | Hallazgo |
| `header-framing` | CSP frame-ancestors o X-Frame-Options | Hallazgo |
| `header-referrer-policy` | Referrer-Policy | Hallazgo |
| `header-permissions-policy` | Permissions-Policy | Hallazgo |
| `cookie-secure` | Secure en cookies de sesión observadas | No aplica sin cookie de sesión |
| `cookie-httponly` | HttpOnly en cookies de sesión observadas | No aplica sin cookie de sesión |
| `cookie-samesite` | SameSite en cookies de sesión observadas | No aplica sin cookie de sesión |

Estos controles suman al índice solo cuando están medidos. Un control de cookie no observado no resta puntos.

## Familias de Argon que no se pueden probar con una respuesta normal

Las doce familias siguientes aparecen en el catálogo v2 como `not_evaluated`, con peso cero. Sus controles y pruebas de origen se revisaron en el repositorio Argon Defender; no representan un escaneo del sitio del cliente.

| ID | Familia de Argon Defender | Referencia de implementación/pruebas | Evidencia futura necesaria |
|---|---|---|---|
| `argon-sqli` | Firmas de inyección SQL | `src/proxy.py`; `tests/test_proxy.py` | Prueba de solicitudes autorizada en staging |
| `argon-xss` | Firmas de XSS activo | `src/proxy.py`; `tests/test_proxy.py` | Prueba contextual autorizada en staging |
| `argon-command-injection` | Firmas de inyección de comandos | `src/proxy.py`; `tests/test_proxy.py` | Prueba autorizada en staging y revisión de la aplicación |
| `argon-route-policy` | Políticas de rutas y métodos | `src/app_route_policy.py`, `src/proxy.py`; `tests/test_app_route_policy.py` | Manifiesto y prueba autorizada por método |
| `argon-request-size` | Límites del cuerpo de solicitud | `src/proxy.py`; `tests/test_proxy.py` | Configuración o prueba acotada en staging |
| `argon-decompression-bounds` | Límites de gzip/descompresión | `src/proxy.py`; `tests/test_proxy.py` | Configuración o prueba acotada en staging |
| `argon-json-depth` | Profundidad máxima de JSON | `src/proxy.py`; `tests/test_proxy.py` | Configuración del parser o prueba acotada en staging |
| `argon-behavior-overload` | Cadencia, comportamiento y sobrecarga | `src/proxy.py`; `tests/test_proxy.py`, corpus de comportamiento | Tráfico gradual autorizado y métricas de concurrencia/latencia |
| `argon-session-isolation` | Separación de actores por sesión | `src/proxy.py`; `tests/test_actor_key_session.py` | Pruebas con sesiones independientes |
| `argon-verified-identity` | Identidad verificada por autorización | `src/proxy.py`; `tests/test_verified_actor.py` | Pruebas con identidades de staging y revisión del adaptador |
| `argon-tls-provenance` | Confianza en metadatos JA3/JA4 | `src/proxy.py`; `tests/test_proxy.py` | Revisión de topología y proxy TLS de confianza |
| `argon-upstream-timeout` | Timeout de lectura del origen | `src/proxy.py`; `tests/test_upstream_read_timeout.py` | Ensayo controlado de timeout y métricas del origen |

La cobertura del reporte cuenta los 22 IDs versionados. El índice se calcula solo con controles observados; los doce pendientes y los controles `not_applicable` no se convierten en aprobaciones ni en fallas. Una futura integración activa deberá ser independiente, optativa, limitada a dominios verificados y versionada antes de cambiar el catálogo.
