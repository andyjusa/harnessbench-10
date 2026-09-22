#!/usr/bin/env python3
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
