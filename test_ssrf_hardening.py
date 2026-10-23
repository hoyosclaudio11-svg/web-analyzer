"""Regression checks for SSRF address scope and bounded response reads."""

from unittest.mock import Mock, patch

import pytest

import analyzer


@pytest.mark.parametrize("address", [
    "100.64.0.1",       # carrier-grade NAT
    "192.0.2.1",        # documentation range
    "198.51.100.1",     # documentation range
    "203.0.113.1",      # documentation range
    "240.0.0.1",        # reserved IPv4 range
    "2001:db8::1",      # documentation IPv6 range
])
def test_non_global_resolved_ip_is_rejected(address):
    with patch(
        "analyzer.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", (address, 80))],
    ):
        ok, reason = analyzer._is_public_url("https://example.test/")

    assert not ok
    assert "globalmente enrutable" in reason


def test_response_stream_is_bounded_even_without_content_length():
    response = Mock()
    response.is_redirect = False
    response.status_code = 200
    response.headers = {}
    response.iter_content.return_value = (
        b"a" * analyzer._MAX_RESPONSE_BYTES,
        b"b",
    )

    session = Mock()
    session.get.return_value = response
    with patch(
        "analyzer.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", ("1.2.3.4", 80))],
    ), patch("analyzer.requests.Session", return_value=session):
        with pytest.raises(ValueError, match="Respuesta demasiado grande"):
            analyzer._safe_get("https://example.test/")

    assert session.get.call_args.kwargs["stream"] is True
    response.close.assert_called_once()
