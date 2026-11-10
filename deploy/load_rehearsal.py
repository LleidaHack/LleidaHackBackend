#!/usr/bin/env python3
"""Bounded read-only rehearsal against a local candidate, never production."""

import argparse
import concurrent.futures
import json
import time
import urllib.request
from urllib.parse import urlsplit


def exercise(origin, event_id, clients=3, rounds=10):
    parsed = urlsplit(origin)
    if (
        parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
        or parsed.scheme != "http"
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Load rehearsals require a local HTTP origin")
    if not 1 <= clients <= 8 or not 1 <= rounds <= 30 or event_id < 1:
        raise ValueError("Use 1-8 clients, 1-30 rounds and a positive event ID")
    urls = [
        origin.rstrip("/") + "/health/ready",
        origin.rstrip("/") + f"/v1/operations/{event_id}/public",
    ]

    def client(index):
        results = []
        for n in range(rounds):
            start = time.monotonic()
            try:
                with urllib.request.urlopen(
                    urls[(index + n) % 2], timeout=10
                ) as response:
                    response.read()
                    ok = response.status == 200
            except OSError:
                ok = False
            results.append((ok, (time.monotonic() - start) * 1000))
            time.sleep(max(0, 1 - (time.monotonic() - start)))
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=clients) as executor:
        results = [
            result for batch in executor.map(client, range(clients)) for result in batch
        ]
    durations = sorted(duration for _, duration in results)
    return {
        "requests": len(results),
        "failures": sum(not ok for ok, _ in results),
        "p95_ms": round(durations[min(len(durations) - 1, int(len(durations) * 0.95))]),
        "max_ms": round(max(durations)),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("origin")
    parser.add_argument("event_id", type=int)
    parser.add_argument("--clients", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=10)
    args = parser.parse_args()
    result = exercise(args.origin, args.event_id, args.clients, args.rounds)
    print(json.dumps(result))
    raise SystemExit(bool(result["failures"]))
