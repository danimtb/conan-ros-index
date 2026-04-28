#!/usr/bin/env bash
# CI / local checks for this example. Invoked by scripts/ci/run-example-tests.sh and documented in readme.md.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python -m pip install -q --upgrade pip
python -m pip install -q "colcon-common-extensions"

conan install . --output-folder=build -s build_type=Release --build=missing

rosenv_bat=""
rosenv_sh=""
for d in \
  build/build/generators \
  build/Release/generators \
  build/Debug/generators \
  build/generators; do
  if [[ -z "${rosenv_bat}" && -f "${d}/conanrosenv.bat" ]]; then
    rosenv_bat="${d}/conanrosenv.bat"
  fi
  if [[ -z "${rosenv_sh}" && -f "${d}/conanrosenv.sh" ]]; then
    rosenv_sh="${d}/conanrosenv.sh"
  fi
done

is_windows=false
case "${RUNNER_OS:-}" in Windows) is_windows=true ;; esac
if [[ "${OS:-}" == "Windows_NT" ]]; then is_windows=true; fi
case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) is_windows=true ;; esac

# Align with Conan (Release): MSVC/Xcode multi-config defaults to RelWithDebInfo and breaks imported Conan targets.
# Omit --symlink-install: Windows runners often lack symlink creation rights without Developer Mode.
if [[ "${is_windows}" == true ]]; then
  if [[ -z "${rosenv_bat}" ]]; then
    echo "Could not find conanrosenv.bat under build/; adjust paths in ci-commands.sh after conan install."
    exit 1
  fi
  # Git Bash cannot reliably source conanrosenv.sh; use cmd with the MSVC/ROS environment.
  bat_for_cmd="${rosenv_bat//\//\\}"
  cmd.exe //C "call ${bat_for_cmd} && colcon build --cmake-args -DCMAKE_CONFIGURATION_TYPES=Release --event-handlers console_cohesion+"
else
  if [[ -z "${rosenv_sh}" ]]; then
    echo "Could not find conanrosenv.sh under build/; adjust paths in ci-commands.sh after conan install."
    exit 1
  fi
  # shellcheck source=/dev/null
  source "${rosenv_sh}"
  # Pass both flags: Ninja/Makefiles use BUILD_TYPE; Xcode multi-config respects CONFIGURATION_TYPES (ignores BUILD_TYPE).
  colcon build \
    --cmake-args -DCMAKE_BUILD_TYPE=Release \
    --cmake-args -DCMAKE_CONFIGURATION_TYPES=Release \
    --event-handlers console_cohesion+
fi
