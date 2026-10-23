from requests.structures import CaseInsensitiveDict

from security_audit import CATALOG_VERSION, METHODOLOGY_ID, audit_response


def test_secure_response_scores_all_observed_controls():
    headers = CaseInsensitiveDict({
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=()",
    })

    result = audit_response("https://example.test/", headers)

    assert result["metodologia"] == METHODOLOGY_ID
    assert result["puntaje"] == 10
    assert result["resumen"]["observaciones"] == 0
    assert result["resumen"]["evaluados"] == 7
    assert result["resumen"]["catalogo_total"] == 22
    assert result["resumen"]["cobertura_porcentaje"] == 32
    assert result["resumen"]["no_aplica"] == 3
    assert result["resumen"]["no_evaluados"] == 12
    assert len(result["controles"]) == 22
    assert all(control["catalogo_version"] == CATALOG_VERSION for control in result["controles"])


def test_http_and_missing_headers_create_evidence_based_findings():
    result = audit_response("http://example.test/", CaseInsensitiveDict())

    assert result["puntaje"] == 0
    assert result["resumen"]["observaciones"] >= 7
    assert result["resumen"]["no_aplica"] == 3
    assert all("valor" not in control for control in result["controles"])


def test_no_session_cookie_is_not_scored_as_a_failure():
    headers = CaseInsensitiveDict({"Set-Cookie": "theme=dark; Path=/"})

    result = audit_response("https://example.test/", headers)
    cookie_controls = [c for c in result["controles"] if c["id"].startswith("cookie-")]

    assert len(cookie_controls) == 3
    assert all(c["estado"] == "not_applicable" for c in cookie_controls)
    assert all(c["peso"] == 0 for c in cookie_controls)
    assert result["resumen"]["evaluados"] == 7
    assert result["resumen"]["no_evaluados"] == 12


def test_session_cookie_flags_are_checked_without_exposing_values():
    headers = CaseInsensitiveDict({
        "Set-Cookie": "session_token=secret; Path=/; Secure; HttpOnly; SameSite=Lax",
    })

    result = audit_response("https://example.test/", headers)
    cookie_controls = [c for c in result["controles"] if c["id"].startswith("cookie-")]

    assert len(cookie_controls) == 3
    assert all(c["estado"] == "pass" for c in cookie_controls)
    assert result["resumen"]["evaluados"] == 10
    assert result["resumen"]["cobertura_porcentaje"] == 45
    assert "secret" not in str(result)


def test_argon_defense_families_remain_visible_without_affecting_passive_score():
    result = audit_response("https://example.test/", CaseInsensitiveDict())

    active_controls = [
        control for control in result["controles"]
        if control["familia"] == "argon_defensa_activa_o_servidor"
    ]
    assert len(active_controls) == 12
    assert all(control["estado"] == "not_evaluated" for control in active_controls)
    assert all(control["peso"] == 0 for control in active_controls)


def test_frame_ancestors_or_x_frame_options_satisfies_framing_control():
    result = audit_response(
        "https://example.test/",
        CaseInsensitiveDict({"X-Frame-Options": "SAMEORIGIN"}),
    )

    framing = next(c for c in result["controles"] if c["id"] == "header-framing")
    assert framing["estado"] == "pass"
