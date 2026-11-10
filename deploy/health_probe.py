#!/usr/bin/env python3
"""Read-only readiness probe; emits machine-readable status and exits nonzero on failure."""

import argparse
import json
import time
import urllib.error
import urllib.request
from urllib.parse import urlsplit


def probe(origin):
    parsed = urlsplit(origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Use an HTTP origin without credentials, query or fragment")
    url = origin.rstrip("/") + "/health/ready"
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read(4096))
            healthy = response.status == 200 and data.get("status") == "ok"
    except (OSError, ValueError):
        healthy = False
    return {
        "healthy": healthy,
        "duration_ms": round((time.monotonic() - started) * 1000),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    args = parser.parse_args()
    result = probe(args.origin)
    print(json.dumps(result))
    raise SystemExit(0 if result["healthy"] else 1)
