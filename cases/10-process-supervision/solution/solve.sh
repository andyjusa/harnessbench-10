#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/supervise.py" <<'PY'
import os
import signal
import subprocess

def supervise(command, timeout):
    process = subprocess.Popen(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        os.killpg(process.pid, signal.SIGKILL)
        remaining, _ = process.communicate()
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode()
        return {"status": "timeout", "exit_code": None, "stdout": partial + remaining}
    return {
        "status": "success" if process.returncode == 0 else "failure",
        "exit_code": process.returncode,
        "stdout": stdout,
    }
PY
