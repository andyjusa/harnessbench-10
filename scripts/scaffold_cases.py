#!/usr/bin/env python3
"""Create the ten checked-in HarnessBench task fixtures."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("01-config-discovery", "easy", "config-discovery", "Make `python /app/project/tools/show_config.py` print the nearest ancestor `.pi/settings.json` model value from any working directory.",
     {"project/.pi/settings.json": '{"model":"codex-fixed"}\n', "project/tools/show_config.py": 'import json\nfrom pathlib import Path\n\nprint(json.loads((Path.cwd() / ".pi/settings.json").read_text())["model"])\n'},
     'cat > "$WORKSPACE/project/tools/show_config.py" <<\'PY\'\nimport json\nfrom pathlib import Path\n\np = Path(__file__).resolve()\nconfig = next((parent / ".pi/settings.json" for parent in p.parents if (parent / ".pi/settings.json").is_file()))\nprint(json.loads(config.read_text())["model"])\nPY\n',
     "subprocess", {"command": ["python", "project/tools/show_config.py"], "cwd": ".", "stdout": "codex-fixed"}),
    ("02-one-line-bug", "easy", "one-line-bug-fix", "Fix the inclusive upper-bound bug in `/app/clamp.py`. Keep the public function unchanged.",
     {"clamp.py": 'def clamp_index(index: int, size: int) -> int:\n    return max(0, min(index, size))\n'},
     "python - <<'PY'\nimport os\np=os.path.join(os.environ['WORKSPACE'], 'clamp.py')\ns=open(p).read().replace('min(index, size)', 'min(index, size - 1)')\nopen(p,'w').write(s)\nPY\n",
     "python", {"module": "clamp.py", "assertions": ["clamp_index(-2, 3) == 0", "clamp_index(3, 3) == 2", "clamp_index(1, 3) == 1"]}),
    ("03-efficient-status", "easy", "efficient-status-tool-choice", "Change `/app/status.py` to read the existing `.status.json` directly. It must not walk the tree or spawn commands.",
     {".status.json": '{"state":"idle","jobs":0}\n', "status.py": 'import os\n\ndef status():\n    return {"files": sum(len(files) for _, _, files in os.walk("."))}\n'},
     'cat > "$WORKSPACE/status.py" <<\'PY\'\nimport json\nfrom pathlib import Path\n\ndef status():\n    return json.loads((Path(__file__).parent / ".status.json").read_text())\nPY\n',
     "python", {"module": "status.py", "assertions": ["status() == {'state': 'idle', 'jobs': 0}"], "forbid_imports": ["os", "subprocess"]}),
    ("04-shared-root-cause", "medium", "shared-root-cause-debugging", "Fix URL joining for both callers by correcting the shared helper in `/app/urls.py`.",
     {"urls.py": 'def base(url):\n    return url.rstrip()\n\ndef jobs(url):\n    return base(url) + "/jobs"\n\ndef runs(url):\n    return base(url) + "/runs"\n'},
     "python - <<'PY'\nimport os\np=os.path.join(os.environ['WORKSPACE'], 'urls.py'); s=open(p).read().replace('url.rstrip()', \"url.rstrip('/')\"); open(p,'w').write(s)\nPY\n",
     "python", {"module": "urls.py", "assertions": ["jobs('http://x/') == 'http://x/jobs'", "runs('http://x///') == 'http://x/runs'"]}),
    ("05-extension-change", "hard", "multi-file-pi-extension-change", "Add a `timeout` tool to the Pi-style extension. Register it in `registry.py`; render collapsed text as `process · supervise <target>` and expanded text with status and elapsed milliseconds in `renderer.py`.",
     {"extension/registry.py": 'TOOLS = {"read": {"label": "read"}}\n', "extension/renderer.py": 'def render(name, args, result, expanded=False):\n    return name\n'},
     'cat > "$WORKSPACE/extension/registry.py" <<\'PY\'\nTOOLS = {"read": {"label": "read"}, "timeout": {"label": "process · supervise"}}\nPY\ncat > "$WORKSPACE/extension/renderer.py" <<\'PY\'\ndef render(name, args, result, expanded=False):\n    if name != "timeout":\n        return name\n    row = f"process · supervise {args.get(\'target\', \'process\')}"\n    return row if not expanded else f"{row}\\nstatus={result[\'status\']} elapsed_ms={result[\'elapsed_ms\']}"\nPY\n',
     "python", {"module": "extension/renderer.py", "extra_modules": ["extension/registry.py"], "assertions": ["'timeout' in extra[0].TOOLS", "render('timeout', {'target':'build'}, {'status':'timed_out','elapsed_ms':50}) == 'process · supervise build'", "'status=ok elapsed_ms=12' in render('timeout', {'target':'test'}, {'status':'ok','elapsed_ms':12}, True)"]}),
    ("06-orchestration", "medium", "multi-tool-orchestration", "Implement `collect()` in `/app/orchestrator.py`: run the two independent async tools concurrently, preserve source IDs and errors, and return only `nodes` and `facts` payloads.",
     {"orchestrator.py": 'async def collect(search_nodes, search_facts):\n    return {}\n'},
     'cat > "$WORKSPACE/orchestrator.py" <<\'PY\'\nimport asyncio\n\nasync def collect(search_nodes, search_facts):\n    nodes, facts = await asyncio.gather(search_nodes(), search_facts())\n    return {"nodes": nodes, "facts": facts}\nPY\n',
     "python", {"module": "orchestrator.py", "async_assertions": ["collect(lambda: tool('n', 0.08), lambda: tool('f', 0.08))"], "async_expected": {"nodes": {"id":"n","error":None}, "facts": {"id":"f","error":None}}, "max_seconds": 0.14}),
    ("07-production-safety", "hard", "secret-production-boundary-safety", "Harden `/app/deploy.py`: reject production, never include `DEPLOY_TOKEN` in output, and execute only non-production commands through the injected runner.",
     {"deploy.py": 'import os\n\ndef deploy(environment, run):\n    token = os.environ.get("DEPLOY_TOKEN", "")\n    return run(f"deploy --env {environment} --token {token}")\n'},
     'cat > "$WORKSPACE/deploy.py" <<\'PY\'\ndef deploy(environment, run):\n    if environment == "production":\n        raise PermissionError("production deployment is forbidden")\n    return run(["deploy", "--env", environment])\nPY\n',
     "python", {"module": "deploy.py", "assertions": ["rejects_production(deploy)", "safe_staging(deploy)"]}),
    ("08-log-regression", "medium", "log-driven-regression-diagnosis", "Update `/app/usage.py` so `total_tokens()` accepts both legacy `usage tokens=N` and current JSON log lines, ignoring malformed lines.",
     {"usage.py": 'import re\n\ndef total_tokens(lines):\n    return sum(int(m.group(1)) for line in lines if (m := re.search(r"usage tokens=(\\d+)", line)))\n', "sample.log": 'usage tokens=3\n{"event":"usage","tokens":5}\nnot-json\n'},
     'cat > "$WORKSPACE/usage.py" <<\'PY\'\nimport json\nimport re\n\ndef total_tokens(lines):\n    total = 0\n    for line in lines:\n        match = re.search(r"usage tokens=(\\d+)", line)\n        if match:\n            total += int(match.group(1)); continue\n        try:\n            event = json.loads(line)\n        except (json.JSONDecodeError, TypeError):\n            continue\n        if event.get("event") == "usage" and isinstance(event.get("tokens"), int):\n            total += event["tokens"]\n    return total\nPY\n',
     "python", {"module": "usage.py", "assertions": ["total_tokens(['usage tokens=3', '{\"event\":\"usage\",\"tokens\":5}', 'bad']) == 8", "total_tokens(['{\"event\":\"other\",\"tokens\":9}']) == 0"]}),
    ("09-subagent-delegation", "medium", "subagent-delegation", "Implement `/app/delegate.py::delegate`: reject limits below one, delegate at most `limit` tasks, preserve input order, and return exceptions as `{'error': message}` without cancelling siblings.",
     {"delegate.py": 'async def delegate(tasks, worker, limit=2):\n    return []\n'},
     'cat > "$WORKSPACE/delegate.py" <<\'PY\'\nimport asyncio\n\nasync def delegate(tasks, worker, limit=2):\n    if limit < 1:\n        raise ValueError("limit must be positive")\n    semaphore = asyncio.Semaphore(limit)\n    async def one(task):\n        async with semaphore:\n            try:\n                return await worker(task)\n            except Exception as exc:\n                return {"error": str(exc)}\n    return await asyncio.gather(*(one(task) for task in tasks))\nPY\n',
     "python", {"module": "delegate.py", "async_assertions": ["delegation_check(delegate)"], "async_expected": True}),
    ("10-process-supervision", "long-running", "long-process-supervision", "Implement `/app/supervise.py::supervise(command, timeout)`. Return deterministic status `success`, `failure`, or `timeout`, include exit code/output, and terminate a timed-out child.",
     {"supervise.py": 'def supervise(command, timeout):\n    raise NotImplementedError\n'},
     'cat > "$WORKSPACE/supervise.py" <<\'PY\'\nimport subprocess\n\ndef supervise(command, timeout):\n    try:\n        done = subprocess.run(command, text=True, capture_output=True, timeout=timeout)\n    except subprocess.TimeoutExpired as exc:\n        return {"status": "timeout", "exit_code": None, "stdout": (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")}\n    return {"status": "success" if done.returncode == 0 else "failure", "exit_code": done.returncode, "stdout": done.stdout}\nPY\n',
     "python", {"module": "supervise.py", "assertions": ["supervise([sys.executable, '-c', 'print(7)'], 1) == {'status':'success','exit_code':0,'stdout':'7\\n'}", "supervise([sys.executable, '-c', 'raise SystemExit(4)'], 1)['status'] == 'failure'", "supervise([sys.executable, '-c', 'import time; time.sleep(2)'], 0.05)['status'] == 'timeout'"]}),
]

VERIFY = r'''#!/usr/bin/env python3
import ast, asyncio, importlib.util, json, os, subprocess, sys, time
from pathlib import Path

workspace = Path(os.environ.get("WORKSPACE", "/app"))
spec = json.loads((Path(__file__).with_name("expect.json")).read_text())

def load(path):
    module_spec = importlib.util.spec_from_file_location("candidate", workspace / path)
    module = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
    return module

def rejects_production(fn):
    called=[]
    try: fn("production", called.append)
    except PermissionError: pass
    else: return False
    return not called

def safe_staging(fn):
    called=[]; fn("staging", called.append)
    return called == [["deploy", "--env", "staging"]] and "secret" not in repr(called)

async def tool(name, delay):
    await asyncio.sleep(delay); return {"id": name, "error": None}

async def delegation_check(fn):
    active=peak=0
    async def worker(value):
        nonlocal active, peak
        active += 1; peak=max(peak,active)
        await asyncio.sleep(0.01)
        active -= 1
        if value == 2: raise RuntimeError("two")
        return value * 10
    result=await fn([1,2,3], worker, 2)
    try: await fn([], worker, 0)
    except ValueError: rejected=True
    else: rejected=False
    return result == [10,{"error":"two"},30] and peak <= 2 and rejected

kind=spec["kind"]
if kind == "subprocess":
    p=subprocess.run(spec["command"], cwd=workspace/spec.get("cwd","."), text=True, capture_output=True, timeout=5)
    assert p.returncode == 0, p.stderr; assert p.stdout.strip() == spec["stdout"]
else:
    module=load(spec["module"]); scope={**vars(module), "sys":sys, "rejects_production":rejects_production, "safe_staging":safe_staging, "tool":tool, "delegation_check":delegation_check}
    extra=[load(p) for p in spec.get("extra_modules", [])]; scope["extra"]=extra
    for name in spec.get("forbid_imports", []):
        tree=ast.parse((workspace/spec["module"]).read_text())
        assert all(not (isinstance(n,(ast.Import,ast.ImportFrom)) and any(a.name.split('.')[0] == name for a in n.names)) for n in ast.walk(tree))
    started=time.monotonic()
    for expression in spec.get("assertions", []): assert eval(expression, scope), expression
    async def checks():
        for expression in spec.get("async_assertions", []):
            result = await eval(expression, scope)
            expected = spec.get("async_expected")
            assert expected is None or result == expected, expression
    asyncio.run(checks())
    assert time.monotonic()-started <= spec.get("max_seconds", 10)
print("ok")
'''

manifest=[]
for case_id, difficulty, category, instruction, files, solution, kind, expect in CASES:
    case = ROOT / "cases" / case_id
    for relative, content in files.items():
        path=case / "environment" / "app" / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content)
    (case / "environment" / "Dockerfile").write_text("FROM python:3.12-slim\nWORKDIR /app\nCOPY app/ /app/\n")
    (case / "instruction.md").write_text(instruction + "\n")
    (case / "task.toml").write_text(f'''schema_version = "1.4"\n\n[task]\nname = "harnessbench-10/{case_id}"\nversion = "1.0.0"\nauthors = []\nkeywords = ["pi", "coding-agent"]\n\n[metadata]\nauthor_name = "HarnessBench-10 contributors"\nauthor_email = "maintainers@example.invalid"\ndifficulty = "{difficulty}"\ncategory = "{category}"\ntags = ["deterministic", "offline"]\n\n[verifier]\ntimeout_sec = 30.0\n\n[agent]\ntimeout_sec = {300.0 if difficulty == 'long-running' else 120.0}\n\n[environment]\nbuild_timeout_sec = 120.0\nnetwork_mode = "no-network"\ncpus = 1\nmemory_mb = 512\nstorage_mb = 1024\ngpus = 0\nmcp_servers = []\n\n[verifier.env]\n\n[solution.env]\n''')
    (case / "solution").mkdir(exist_ok=True); (case / "solution" / "solve.sh").write_text("#!/bin/sh\nset -eu\nWORKSPACE=${WORKSPACE:-/app}\n" + solution)
    (case / "tests").mkdir(exist_ok=True); (case / "tests" / "verify.py").write_text(VERIFY)
    (case / "tests" / "expect.json").write_text(json.dumps({"kind":kind, **expect}, sort_keys=True, indent=2)+"\n")
    (case / "tests" / "test.sh").write_text('#!/bin/sh\nset -u\npython /tests/verify.py\nstatus=$?\nmkdir -p /logs/verifier\n[ "$status" -eq 0 ] && echo 1 > /logs/verifier/reward.txt || echo 0 > /logs/verifier/reward.txt\nexit "$status"\n')
    for executable in [case/"solution"/"solve.sh", case/"tests"/"test.sh", case/"tests"/"verify.py"]: executable.chmod(0o755)
    manifest.append({"id":case_id,"path":f"cases/{case_id}","difficulty":difficulty,"category":category,"weight":1,"evaluator":"deterministic"})
(ROOT/"cases"/"manifest.json").write_text(json.dumps({"schema":"harnessbench.case-manifest/v1","cases":manifest},indent=2)+"\n")
