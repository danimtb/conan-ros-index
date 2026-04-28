#!/usr/bin/env bash
# CI / local checks for this example. Invoked by .github/workflows/run-example-tests.sh.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

conan install . --output-folder=build -s build_type=Release -s compiler.cppstd=17 --build=missing

# Conan CMake presets differ by generator:
# - Multi-config (Visual Studio, Xcode): configure preset "conan-default", build "conan-release".
# - Single-config (Ninja, Unix Makefiles): configure + build use "conan-release".
if cmake --preset conan-default; then
  cmake --build --preset conan-release --parallel
elif cmake --preset conan-release; then
  cmake --build --preset conan-release --parallel
else
  echo "No usable Conan CMake preset (tried conan-default then conan-release). See CMakeUserPresets.json after conan install."
  exit 1
fi
