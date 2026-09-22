#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HARNESS=Path(os.environ["PI_HARNESS_ROOT"]).resolve()
AUTH=Path(os.environ.get("PI_AUTH_FILE",Path.home()/".pi/agent/auth.json")).resolve()
MODEL=os.environ.get("PI_BENCH_MODEL","gpt-5.6-sol")
LIMIT=float(os.environ.get("PI_BENCH_COST_LIMIT","10"))
RESULTS=ROOT/"results"/time.strftime("%Y%m%d-%H%M%S")


def metrics(output):
    total={"input_tokens":0,"output_tokens":0,"cache_read_tokens":0,"cache_write_tokens":0,"cost_usd":0.0,"model_turns":0,"tool_calls":0}
    for line in output.splitlines():
        try: event=json.loads(line)
        except json.JSONDecodeError: continue
        if event.get("type")=="message_end" and (message:=event.get("message",{})).get("role")=="assistant":
            usage=message.get("usage",{}); total["model_turns"]+=1
            total["input_tokens"]+=usage.get("input",0); total["output_tokens"]+=usage.get("output",0)
            total["cache_read_tokens"]+=usage.get("cacheRead",0); total["cache_write_tokens"]+=usage.get("cacheWrite",0)
            total["cost_usd"]+=(usage.get("cost") or {}).get("total",0)
            total["tool_calls"]+=sum(block.get("type")=="toolCall" for block in message.get("content",[]))
    return total


def run(case,variant,spent):
    if spent>=LIMIT: raise SystemExit(f"cost limit reached: {spent:.4f}")
    with tempfile.TemporaryDirectory(prefix="harnessbench-") as tmp:
        tmp=Path(tmp); workspace=tmp/"app"; shutil.copytree(case/"environment/app",workspace)
        agent=tmp/"agent"; agent.mkdir(); (agent/"auth.json").symlink_to(AUTH)
        sessions=tmp/"sessions"; sessions.mkdir()
        instruction=(case/"instruction.md").read_text().replace("/app",str(workspace))
        env={**os.environ,"PI_PTC":"1" if variant=="ptc-on" else "0","PI_CODING_AGENT_DIR":str(agent),"PI_CODING_AGENT_SESSION_DIR":str(sessions)}
        command=[process_exec(),str(HARNESS/"main.mjs"),"--print","--mode","json","--provider","openai-codex","--model",MODEL,"--thinking","low",instruction]
        started=time.monotonic()
        try: proc=subprocess.run(command,cwd=workspace,env=env,text=True,capture_output=True,timeout=180)
        except subprocess.TimeoutExpired as exc:
            output=(exc.stdout or "")+(exc.stderr or ""); proc=None
        elapsed=time.monotonic()-started; data=metrics(output if proc is None else proc.stdout+proc.stderr)
        verify_env={**os.environ,"WORKSPACE":str(workspace)}
        verified=subprocess.run([sys.executable,case/"tests/verify.py"],env=verify_env,text=True,capture_output=True,timeout=15)
        result={"schema":"harnessbench.result/v1","case_id":case.name,"variant":variant,"correct":verified.returncode==0,"verifier_result":int(verified.returncode==0),"wall_time_seconds":elapsed,"backend_calls":data["model_turns"],**data,"retries":0,"timeouts":int(proc is None),"failures":[] if proc is not None and proc.returncode==0 and verified.returncode==0 else [("timeout" if proc is None else f"agent-exit-{proc.returncode}"),*([] if verified.returncode==0 else [verified.stderr[-1000:] or verified.stdout[-1000:]])]}
        return result,output if proc is None else proc.stdout+proc.stderr


def process_exec():
    return shutil.which("node") or "node"


def main():
    RESULTS.mkdir(parents=True)
    cases=[ROOT/item["path"] for item in json.loads((ROOT/"cases/manifest.json").read_text())["cases"]]
    spent=0.0
    for case in cases:
        for variant in ("ptc-off","ptc-on"):
            result,log=run(case,variant,spent); spent+=result["cost_usd"]
            stem=f"{case.name}--{variant}"; (RESULTS/f"{stem}.json").write_text(json.dumps(result,indent=2)+"\n"); (RESULTS/f"{stem}.jsonl").write_text(log)
            print(f"{stem}: correct={result['correct']} cost={result['cost_usd']:.4f} total={spent:.4f}",flush=True)
            if spent>LIMIT: raise SystemExit(f"cost limit exceeded: {spent:.4f}")
    print(f"RESULTS={RESULTS}\nTOTAL_COST={spent:.4f}")

if __name__=="__main__": main()
