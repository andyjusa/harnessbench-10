#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
cat > "$WORKSPACE/deploy.py" <<'PY'
def deploy(environment, run):
    if environment == "production":
        raise PermissionError("production deployment is forbidden")
    return run(["deploy", "--env", environment])
PY
