#!/usr/bin/env bash
# CI / local checks for this example. Invoked by .github/workflows/run-example-tests.sh and documented in readme.md.
set -euo pipefail
export PS4='+ ${BASH_SOURCE[0]}:${LINENO}: '
set -x
cd "$(dirname "${BASH_SOURCE[0]}")"

conan install -s compiler.cppstd=17 --build=missing
conan build -s compiler.cppstd=17 --build=missing
