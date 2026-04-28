#!/usr/bin/env bash
# CI for this example; see .github/workflows/run-example-tests.sh and readme.md.
set -euo pipefail
export PS4='+ ${BASH_SOURCE[0]}:${LINENO}: '
set -x
cd "$(dirname "${BASH_SOURCE[0]}")"

python -m pip install -q --upgrade pip colcon-common-extensions
conan install . --output-folder=build -s build_type=Release -s compiler.cppstd=17 --build=missing

g=""
for d in build/build/generators build/Release/generators build/Debug/generators build/generators; do
  [[ -f "$d/conanrosenv.bat" || -f "$d/conanrosenv.sh" ]] && { g="$d"; break; }
done
[[ "$g" ]] || { echo "conanrosenv not found under build/"; exit 1; }

if [[ "${RUNNER_OS:-}" == Windows || "${OS:-}" == Windows_NT || "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; then
  b="${g//\//\\}\conanrosenv.bat"
  cmd.exe //C "call ${b} && colcon build --cmake-args -DCMAKE_CONFIGURATION_TYPES=Release --event-handlers console_cohesion+"
else
  # shellcheck source=/dev/null
  source "$g/conanrosenv.sh"
  colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release --cmake-args -DCMAKE_CONFIGURATION_TYPES=Release --event-handlers console_cohesion+
fi
