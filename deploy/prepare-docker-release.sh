#!/usr/bin/env bash
# Build and validate a candidate. Never starts/stops services or runs migrations.
set -euo pipefail
umask 077
SHA=${1:?Usage: prepare-docker-release.sh COMMIT RELEASE_DIRECTORY}
DEST=${2:?Release directory is required}
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo 'A full commit SHA is required' >&2; exit 1; }
cd "$(git rev-parse --show-toplevel)"
test "$(git rev-parse HEAD)" = "$SHA"
test -z "$(git status --porcelain --untracked-files=normal)"
mkdir -p "$DEST"
DEST=$(cd "$DEST" && pwd)
FREE=$(df -Pk "$DEST" | awk 'END {print $4}')
test "$FREE" -ge 2097152 || { echo 'At least 2 GiB free is required to build' >&2; exit 1; }
IMAGE="lleidahack/backend-release:$SHA"
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  test "$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "$SHA"
else
  docker build --label "org.opencontainers.image.revision=$SHA" --tag "$IMAGE" .
fi
docker image inspect "$IMAGE" --format '{{.Id}}' > "$DEST/image-id.txt"
printf '%s\n' "$SHA" > "$DEST/commit.txt"
# Import configuration without network access or production credentials.
docker run --rm --network none \
  -e DATABASE__URL=postgresql://unused:unused@invalid/unused \
  -e SECURITY__SECRET_KEY=build-validation-signing-key-not-production \
  -e SECURITY__SERVICE_TOKEN=build-validation-service-key-not-production \
  --entrypoint python "$IMAGE" -c \
  'from src.configuration.Settings import settings; from src import imports; print("Candidate imports validated")'
echo "Prepared $IMAGE; production was not restarted and no database was migrated."
