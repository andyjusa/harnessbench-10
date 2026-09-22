import json
from pathlib import Path

print(json.loads((Path.cwd() / ".pi/settings.json").read_text())["model"])
