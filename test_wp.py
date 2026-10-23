"""Manual, read-only WordPress credential check.

This file is intentionally excluded from pytest's default offline test suite.
Run it explicitly only when the owner has set the two environment variables.
"""

from __future__ import annotations

import os
import sys

import requests


def main() -> int:
    user = os.environ.get("WEBANALYZER_WP_USER")
    password = os.environ.get("WEBANALYZER_WP_APP_PASSWORD")
    if not user or not password:
        print("Set WEBANALYZER_WP_USER and WEBANALYZER_WP_APP_PASSWORD to run this check.", file=sys.stderr)
        return 2

    try:
        response = requests.get(
            "https://webanalyzer.com.ar/web/wp-json/wp/v2/users/me",
            auth=(user, password),
            timeout=15,
            allow_redirects=False,
        )
    except requests.RequestException as error:
        print(f"WordPress check failed: {type(error).__name__}", file=sys.stderr)
        return 1

    print(f"WordPress credential check: HTTP {response.status_code}")
    return 0 if response.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
