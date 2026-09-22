#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
python3 - <<'PY'
import os
p=os.path.join(os.environ['WORKSPACE'], 'clamp.py')
s=open(p).read().replace('min(index, size)', 'min(index, size - 1)')
open(p,'w').write(s)
PY
