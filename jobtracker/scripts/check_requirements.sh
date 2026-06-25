#!/usr/bin/env bash
# Fail closed if src/requirements.txt is stale relative to src/requirements.in.
#
# The tofu lambda-function module installs requirements.txt directly and ignores
# uv.lock, so a stale requirements.txt would ship the wrong dependency set to the
# Lambda (e.g. a missing new import -> cold-start ImportError, or drifted versions).
# This recompiles the pinned set with the SAME constraints the deploy install uses
# and refuses to proceed if it differs from the committed file. See issue #2.
set -euo pipefail

cd "$(dirname "$0")/.."  # -> jobtracker/

expected=$(uv pip compile src/requirements.in \
  --python-platform aarch64-manylinux2014 --python-version 3.12 \
  --only-binary :all: --no-header --no-annotate 2>/dev/null)

# Committed pins, minus the generated-header comment lines.
actual=$(grep -vE '^[[:space:]]*#' src/requirements.txt)

if [ "$expected" != "$actual" ]; then
  echo "ERROR: src/requirements.txt is stale vs src/requirements.in." >&2
  echo "Regenerate it (command is in src/requirements.in) and commit the result." >&2
  echo "--- committed (left) vs expected (right) ---" >&2
  diff <(printf '%s\n' "$actual") <(printf '%s\n' "$expected") >&2 || true
  exit 1
fi

echo "OK: src/requirements.txt is in sync with src/requirements.in."
