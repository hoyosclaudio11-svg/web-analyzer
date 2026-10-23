"""Passive security checks for WebAnalyzer, informed by Argon Defender controls.

This module evaluates only evidence already present in a page response. It
does not send exploit payloads, enumerate sensitive paths, or run Argon CLI.
"""

from __future__ import annotations

from urllib.parse import urlsplit


METHODOLOGY_ID = "argon-defender-passive-v1"
METHODOLOGY_NAME = "Índice Argon de seguridad web, basado en metodología Argon Defender"
CATALOG_VERSION = "argon-security-controls-v2"
CATALOG_SIZE = 22

_SECURITY_COOKIES = (
    "session", "sess", "auth", "token", "jwt", "sid", "wordpress_logged_in",
)

# Argon Defender method families which cannot be established from a normal
# page response. They stay visible in coverage but never affect the score.
_ARGON_CONTROLS_REQUIRING_OTHER_EVIDENCE = (
    (
        "argon-sqli", "Firmas de inyección SQL",
        "Las firmas SQLi requieren solicitudes controladas; esta auditoría pasiva no envía payloads.",
        "Prueba autorizada de la capa de defensa y revisión del código de la aplicación.",
    ),
    (
        "argon-xss", "Firmas de XSS activo",
        "La detección de XSS requiere evaluar entradas y respuestas con casos controlados.",
        "Prueba autorizada de la capa de defensa y revisión contextual de la aplicación.",
    ),
    (
        "argon-command-injection", "Inyección de comandos",
        "Una respuesta HTML normal no demuestra cómo se filtran parámetros o cuerpos de solicitudes.",
        "Prueba autorizada sobre un entorno de staging y revisión del manejo de procesos.",
    ),
    (
        "argon-route-policy", "Política de rutas y métodos",
        "La URL inicial no permite inferir qué rutas o métodos están cubiertos por una política.",
        "Manifiesto de rutas y pruebas autorizadas por método.",
    ),
    (
        "argon-request-size", "Límites de tamaño de solicitud",
        "El tamaño de la respuesta no demuestra los límites de cuerpo aceptados por el servidor.",
        "Configuración del servidor o prueba autorizada de límites en staging.",
    ),
    (
        "argon-decompression-bounds", "Límites de descompresión",
        "Una respuesta no revela los límites de descompresión ni la protección ante cuerpos comprimidos.",
        "Configuración del servidor o prueba autorizada de cuerpos comprimidos en staging.",
    ),
    (
        "argon-json-depth", "Profundidad de JSON",
        "La respuesta HTML no revela límites de anidamiento al procesar JSON.",
        "Configuración del parser y prueba autorizada de profundidad en staging.",
    ),
    (
        "argon-behavior-overload", "Cadencia, comportamiento y sobrecarga",
        "Una petición aislada no mide patrones temporales, carga concurrente ni falsos positivos.",
        "Prueba de tráfico gradual en staging y mediciones de concurrencia/latencia.",
    ),
    (
        "argon-session-isolation", "Aislamiento por sesión",
        "La respuesta pública no demuestra que el historial de una sesión esté separado de otras.",
        "Pruebas con sesiones independientes y revisión de la configuración del proxy.",
    ),
    (
        "argon-verified-identity", "Identidad verificada",
        "No se puede confirmar desde una respuesta pública cómo el backend autentica o separa identidades.",
        "Revisión del adaptador de autorización y pruebas con identidades de staging.",
    ),
    (
        "argon-tls-provenance", "Procedencia de señales TLS",
        "Una respuesta HTTP no demuestra que las huellas TLS provengan de un terminador confiable.",
        "Revisión de la topología TLS y de los encabezados del proxy de confianza.",
    ),
    (
        "argon-upstream-timeout", "Timeouts del origen",
        "Una sola respuesta no mide los timeouts del upstream o el presupuesto de lectura.",
        "Pruebas de timeout en staging y métricas del proxy/origen.",
    ),
)


def _headers_get(headers, name: str) -> str:
    if not callable(getattr(headers, "get", None)) or not callable(getattr(headers, "items", None)):
        return ""
    try:
        value = headers.get(name, "")
    except (AttributeError, TypeError):
        value = ""
    return str(value or "").strip()


def _set_cookie_values(headers, raw_headers=None) -> list[str]:
    """Read individual Set-Cookie fields without logging cookie values."""
    raw_headers = raw_headers or getattr(getattr(headers, "raw", None), "headers", None)
    for getter_name in ("getlist", "get_all"):
        getter = getattr(raw_headers, getter_name, None)
        if callable(getter):
            try:
                return [str(value) for value in getter("Set-Cookie") if value]
            except (KeyError, TypeError, AttributeError):
                pass
    value = _headers_get(headers, "Set-Cookie")
    return [value] if value else []


def _control(control_id: str, title: str, status: str, severity: str,
             evidence: str, weight: float = 0, recommendation: str = "",
             family: str = "seguridad_http_observable") -> dict:
    return {
        "id": control_id,
        "titulo": title,
        "estado": status,
        "gravedad": severity,
        "evidencia": evidence,
        "peso": weight,
        "recomendacion": recommendation,
        "catalogo_version": CATALOG_VERSION,
        "familia": family,
    }


def audit_response(url: str, headers, raw_headers=None) -> dict:
    """Return a reproducible, passive score from observable response controls."""
    parsed = urlsplit(url)
    https = parsed.scheme.lower() == "https"
    controls = [
        _control(
            "transport-https", "Conexión HTTPS", "pass" if https else "issue",
            "alta", "El análisis se completó mediante TLS verificado." if https
            else "La URL final usa HTTP.", 2.0,
            "Publicar el sitio bajo HTTPS y redirigir todas las solicitudes HTTP.",
        ),
    ]

    hsts = _headers_get(headers, "Strict-Transport-Security")
    controls.append(_control(
        "header-hsts", "HSTS", "pass" if https and hsts else "issue",
        "media", "La respuesta incluye Strict-Transport-Security." if https and hsts
        else "No se observó Strict-Transport-Security en la respuesta HTTPS.",
        1.5, "Configurar Strict-Transport-Security después de validar HTTPS en todo el sitio.",
    ))

    csp = _headers_get(headers, "Content-Security-Policy")
    csp_weak = bool(csp and ("default-src *" in csp.lower() or "'unsafe-eval'" in csp.lower()))
    controls.append(_control(
        "header-csp", "Content Security Policy", "issue" if not csp or csp_weak else "pass",
        "alta" if not csp else "media",
        "No se observó Content-Security-Policy." if not csp
        else "La política incluye una directiva amplia o unsafe-eval." if csp_weak
        else "La respuesta incluye Content-Security-Policy.",
        2.0, "Definir una CSP ajustada a los recursos reales y retirar comodines o unsafe-eval cuando sea posible.",
    ))

    nosniff = _headers_get(headers, "X-Content-Type-Options").lower() == "nosniff"
    controls.append(_control(
        "header-nosniff", "Protección contra MIME sniffing", "pass" if nosniff else "issue",
        "baja", "X-Content-Type-Options: nosniff está presente." if nosniff
        else "No se observó X-Content-Type-Options: nosniff.",
        1.0, "Enviar X-Content-Type-Options: nosniff.",
    ))

    xfo = _headers_get(headers, "X-Frame-Options").upper()
    frame_ancestors = bool(csp and "frame-ancestors" in csp.lower())
    frame_protected = xfo in {"DENY", "SAMEORIGIN"} or frame_ancestors
    controls.append(_control(
        "header-framing", "Protección contra carga en marcos", "pass" if frame_protected else "issue",
        "media", "X-Frame-Options o CSP frame-ancestors está configurado." if frame_protected
        else "No se observó una política que restrinja la carga en marcos.",
        1.0, "Configurar CSP frame-ancestors o X-Frame-Options según el uso previsto.",
    ))

    referrer = _headers_get(headers, "Referrer-Policy")
    controls.append(_control(
        "header-referrer-policy", "Referrer-Policy", "pass" if referrer else "issue",
        "baja", "La respuesta incluye Referrer-Policy." if referrer
        else "No se observó Referrer-Policy.",
        0.75, "Configurar una Referrer-Policy adecuada, por ejemplo strict-origin-when-cross-origin.",
    ))

    permissions = _headers_get(headers, "Permissions-Policy")
    controls.append(_control(
        "header-permissions-policy", "Permissions-Policy", "pass" if permissions else "issue",
        "informativa", "La respuesta incluye Permissions-Policy." if permissions
        else "No se observó Permissions-Policy.",
        0.5, "Deshabilitar las funciones del navegador que el sitio no utiliza.",
    ))

    cookie_fields = _set_cookie_values(headers, raw_headers)
    session_cookies = [
        value for value in cookie_fields
        if any(marker in value.partition("=")[0].lower() for marker in _SECURITY_COOKIES)
    ]
    if session_cookies:
        for flag, label, weight, recommendation in (
            ("secure", "Secure", 0.5, "Agregar Secure a las cookies de sesión."),
            ("httponly", "HttpOnly", 0.5, "Agregar HttpOnly a las cookies de autenticación."),
            ("samesite", "SameSite", 0.5, "Definir SameSite=Lax o Strict según el flujo de acceso."),
        ):
            missing = sum(flag not in cookie.lower() for cookie in session_cookies)
            controls.append(_control(
                f"cookie-{flag}", f"Cookies de sesión: {label}", "issue" if missing else "pass",
                "media" if flag != "samesite" else "baja",
                f"{missing} de {len(session_cookies)} cookies de sesión no muestran {label}."
                if missing else f"Las {len(session_cookies)} cookies de sesión muestran {label}.",
                weight, recommendation, family="sesion_y_cookies",
            ))
    else:
        controls.extend([
            _control(
                f"cookie-{flag}", f"Cookies de sesión: {label}", "not_applicable",
                "informativa", "No se observó una cookie de sesión reconocible en esta respuesta.",
                family="sesion_y_cookies",
            )
            for flag, label in (("secure", "Secure"), ("httponly", "HttpOnly"), ("samesite", "SameSite"))
        ])

    controls.extend(
        _control(
            control_id, title, "not_evaluated", "informativa", evidence,
            recommendation=recommendation, family="argon_defensa_activa_o_servidor",
        )
        for control_id, title, evidence, recommendation
        in _ARGON_CONTROLS_REQUIRING_OTHER_EVIDENCE
    )

    scored = [item for item in controls if item["peso"] > 0]
    total_weight = sum(item["peso"] for item in scored)
    passed_weight = sum(item["peso"] for item in scored if item["estado"] == "pass")
    score = round(10 * passed_weight / total_weight, 1) if total_weight else 0.0
    evaluated = sum(item["estado"] in {"pass", "issue"} for item in controls)
    return {
        "metodologia": METHODOLOGY_ID,
        "nombre_metodologia": METHODOLOGY_NAME,
        "catalogo_version": CATALOG_VERSION,
        "puntaje": score,
        "controles": controls,
        "resumen": {
            "aprobados": sum(item["estado"] == "pass" for item in controls),
            "observaciones": sum(item["estado"] == "issue" for item in controls),
            "sin_evidencia": sum(item["estado"] == "not_observed" for item in controls),
            "no_evaluados": sum(item["estado"] == "not_evaluated" for item in controls),
            "no_aplica": sum(item["estado"] == "not_applicable" for item in controls),
            "evaluados": evaluated,
            "catalogo_total": CATALOG_SIZE,
            "cobertura_porcentaje": round(100 * evaluated / CATALOG_SIZE),
        },
        "limites": [
            "Evaluación pasiva de la respuesta y las cabeceras visibles.",
            "No mide la configuración interna de la base de datos, el balanceador ni las reglas del servidor.",
            "Las doce familias de Argon que requieren pruebas activas o datos del servidor se muestran como no evaluadas y no afectan al puntaje.",
        ],
    }
