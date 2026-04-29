#!/usr/bin/env bash
# CI for this example; see .github/workflows/run-example-tests.sh and readme.md.
set -euo pipefail
export PS4='+ ${BASH_SOURCE[0]}:${LINENO}: '
set -x
cd "$(dirname "${BASH_SOURCE[0]}")"

python -m pip install -q --upgrade pip colcon-common-extensions
conan install -s compiler.cppstd=17 --build=missing

if [[ "${RUNNER_OS:-}" == Windows || "${OS:-}" == Windows_NT ]]; then
  cmd.exe //C "call build/build/generators/conanrosenv.bat && colcon build --event-handlers console_cohesion+"
else
  source "build/build/generators/conanrosenv.sh"
  colcon build --event-handlers console_cohesion+
fi
