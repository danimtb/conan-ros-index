#!/usr/bin/env bash
# Discover and run each example's ci-commands.sh (repo-local test entrypoints).
# CI: invoked with an absolute path (see conan-create-ros-kilted.yml). Local: run from repo root or pass absolute path.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

failed=0
shopt -s nullglob
for script in examples/*/ci-commands.sh; do
  name="$(basename "$(dirname "$script")")"
  echo "::group::Example: ${name}"
  if (cd "$(dirname "$script")" && bash ./ci-commands.sh); then
    echo "::endgroup::"
  else
    echo "::endgroup::"
    echo "::error::Example ${name} failed (see ci-commands.sh in that folder)"
    failed=1
  fi
done
shopt -u nullglob

exit "${failed}"
