#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HARNESS=Path(os.environ["PI_HARNESS_ROOT"]).resolve()
AUTH=Path(os.environ.get("PI_AUTH_FILE",Path.home()/".pi/agent/auth.json")).resolve()
MODEL=os.environ.get("PI_BENCH_MODEL","gpt-5.6-sol")
LIMIT=float(os.environ.get("PI_BENCH_COST_LIMIT","10"))
RESULTS=ROOT/"results"/f"orchestrator-{time.strftime('%Y%m%d-%H%M%S')}"


def parse(output):
    data={"input_tokens":0,"output_tokens":0,"cache_read_tokens":0,"cache_write_tokens":0,"cost_usd":0.0,"model_turns":0,"tool_calls":0}
    final=""
    for line in output.splitlines():
        try: event=json.loads(line)
        except json.JSONDecodeError: continue
        if event.get("type")=="message_end" and (message:=event.get("message",{})).get("role")=="assistant":
            usage=message.get("usage",{}); data["model_turns"]+=1
            data["input_tokens"]+=usage.get("input",0); data["output_tokens"]+=usage.get("output",0)
            data["cache_read_tokens"]+=usage.get("cacheRead",0); data["cache_write_tokens"]+=usage.get("cacheWrite",0)
            data["cost_usd"]+=(usage.get("cost") or {}).get("total",0)
            data["tool_calls"]+=sum(block.get("type")=="toolCall" for block in message.get("content",[]))
            texts=[block.get("text","") for block in message.get("content",[]) if block.get("type")=="text"]
            if texts: final="\n".join(texts)
    return data,final


def invoke(workspace,agent,sessions,prompt,tools,timeout):
    env={**os.environ,"PI_PTC":"0","PI_CODING_AGENT_DIR":str(agent),"PI_CODING_AGENT_SESSION_DIR":str(sessions)}
    command=[shutil.which("node") or "node",str(HARNESS/"main.mjs"),"--print","--mode","json","--provider","openai-codex","--model",MODEL,"--thinking","low","--tools",tools,prompt]
    started=time.monotonic()
    try:
        proc=subprocess.run(command,cwd=workspace,env=env,text=True,capture_output=True,timeout=timeout)
        output=proc.stdout+proc.stderr; failure=None if proc.returncode==0 else f"agent-exit-{proc.returncode}"
    except subprocess.TimeoutExpired as exc:
        output=(exc.stdout or "")+(exc.stderr or ""); failure="timeout"
    data,final=parse(output)
    return data,final,output,time.monotonic()-started,failure


def merge(items):
    keys=["input_tokens","output_tokens","cache_read_tokens","cache_write_tokens","cost_usd","model_turns","tool_calls"]
    return {key:sum(item[key] for item in items) for key in keys}


def run(case,variant,spent):
    if spent>=LIMIT: raise SystemExit(f"cost limit reached: {spent:.4f}")
    with tempfile.TemporaryDirectory(prefix="harnessbench-orch-") as tmp:
        tmp=Path(tmp); workspace=tmp/"app"; shutil.copytree(case/"environment/app",workspace)
        agent=tmp/"agent"; agent.mkdir(); (agent/"auth.json").symlink_to(AUTH)
        sessions=tmp/"sessions"; sessions.mkdir()
        instruction=(case/"instruction.md").read_text().replace("/app",str(workspace))
        stages=[]; logs=[]; failures=[]; started=time.monotonic()
        manifest=next(x for x in MANIFEST if x["id"]==case.name)
        if variant=="solo" or manifest["difficulty"]=="easy":
            plan=[("solo",instruction,"read,bash,edit,write",180)]
        elif manifest["difficulty"]=="medium":
            plan=[("worker","You are the implementation worker. Complete the task and verify the result.\n\n"+instruction,"read,bash,edit,write",180)]
        else:
            scout_prompt="You are a read-only scout. Inspect the workspace and return concise implementation guidance with exact files. Do not modify anything.\n\n"+instruction
            scout,context,log,_,failure=invoke(workspace,agent,sessions,scout_prompt,"read,bash",120)
            stages.append(scout); logs.append(("scout",log)); failures.extend([failure] if failure else [])
            worker_prompt="You are the implementation worker. Complete and verify the task using the scout findings.\n\nTASK:\n"+instruction+"\n\nSCOUT FINDINGS:\n"+context[-12000:]
            plan=[("worker",worker_prompt,"read,bash,edit,write",180),("reviewer","You are a read-only reviewer. Review the completed workspace against this requirement. Do not modify files or run destructive commands.\n\n"+instruction,"read,bash",120)]
        for role,prompt,tools,timeout in plan:
            data,_,log,_,failure=invoke(workspace,agent,sessions,prompt,tools,timeout)
            stages.append(data); logs.append((role,log)); failures.extend([failure] if failure else [])
        elapsed=time.monotonic()-started; data=merge(stages)
        verified=subprocess.run([sys.executable,case/"tests/verify.py"],env={**os.environ,"WORKSPACE":str(workspace)},text=True,capture_output=True,timeout=15)
        if verified.returncode: failures.append(verified.stderr[-1000:] or verified.stdout[-1000:])
        result={"schema":"harnessbench.result/v1","case_id":case.name,"variant":variant,"correct":verified.returncode==0,"verifier_result":int(verified.returncode==0),"wall_time_seconds":elapsed,"backend_calls":data["model_turns"],**data,"retries":0,"timeouts":sum(x=="timeout" for x in failures),"failures":failures,"route":"solo" if variant=="solo" or manifest["difficulty"]=="easy" else "worker" if manifest["difficulty"]=="medium" else "scout-worker-reviewer"}
        return result,"\n".join(f"--- {role} ---\n{log}" for role,log in logs)


def main():
    RESULTS.mkdir(parents=True); spent=0.0
    for case in [ROOT/x["path"] for x in MANIFEST]:
        for variant in ("solo","adaptive"):
            result,log=run(case,variant,spent); spent+=result["cost_usd"]
            stem=f"{case.name}--{variant}"; (RESULTS/f"{stem}.json").write_text(json.dumps(result,indent=2)+"\n"); (RESULTS/f"{stem}.jsonl").write_text(log)
            print(f"{stem}: route={result['route']} correct={result['correct']} cost={result['cost_usd']:.4f} total={spent:.4f}",flush=True)
            if spent>LIMIT: raise SystemExit(f"cost limit exceeded: {spent:.4f}")
    print(f"RESULTS={RESULTS}\nTOTAL_COST={spent:.4f}")

MANIFEST=json.loads((ROOT/"cases/manifest.json").read_text())["cases"]
if __name__=="__main__": main()
