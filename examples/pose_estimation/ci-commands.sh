#!/usr/bin/env bash
# CI / local checks for this example. Invoked by .github/workflows/run-example-tests.sh.
set -euo pipefail
export PS4='+ ${BASH_SOURCE[0]}:${LINENO}: '
set -x
cd "$(dirname "${BASH_SOURCE[0]}")"

conan install -s compiler.cppstd=17 --build=missing

if [[ "${RUNNER_OS:-}" == Windows || "${OS:-}" == Windows_NT ]]; then
  cmd.exe //C "call build/release/generators/conanbuild.bat && cmake --preset conan-release &&cmake --build --preset conan-release"
else
  source "build/release/generators/conanbuild.sh"
  cmake --preset conan-release
  cmake --build --preset conan-release
fi
