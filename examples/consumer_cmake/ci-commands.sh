#!/usr/bin/env bash
# CI / local checks for this example. Invoked by scripts/ci/run-example-tests.sh and documented in readme.md.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

conan install . --output-folder=build -s build_type=Release -s compiler.cppstd=17 --build=missing
conan build . --output-folder=build
