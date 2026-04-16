"""Smoke-test demo_nodes_cpp talker output after sourcing local_setup.bat (Windows)."""

from __future__ import annotations

import subprocess
import sys
import time


def main() -> int:
    proc = subprocess.Popen(
        ["ros2", "run", "demo_nodes_cpp", "talker"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    try:
        deadline = time.time() + 20.0
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    print(proc.stdout.read() or "", end="")
                    print("ERROR: talker exited early", file=sys.stderr)
                    return 1
                time.sleep(0.05)
                continue
            lower = line.lower()
            if "publishing" in lower or "publish" in lower:
                print("demo_smoke: heard talker output — OK")
                return 0
        print("ERROR: timeout waiting for talker output", file=sys.stderr)
        return 1
    finally:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
