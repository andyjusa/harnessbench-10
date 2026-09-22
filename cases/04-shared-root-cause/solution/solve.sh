#!/bin/sh
set -eu
WORKSPACE=${WORKSPACE:-/app}
python3 - <<'PY'
import os
p=os.path.join(os.environ['WORKSPACE'], 'urls.py'); s=open(p).read().replace('url.rstrip()', "url.rstrip('/')"); open(p,'w').write(s)
PY
