#!/usr/bin/env bash
# Deploy the latest validated main commit on the production Docker host.
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"
exec python3 deploy/production_deploy.py "$@"
