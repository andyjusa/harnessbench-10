#!/usr/bin/env python3
"""Validate all task metadata and reference solutions without Docker or models."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections import Counter
from pathlib import Path

from harbor.models.task.config import TaskConfig
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_DIFFICULTIES = {"easy": 3, "medium": 4, "hard": 2, "long-running": 1}
EXPECTED_CATEGORIES = {
    "config-discovery", "one-line-bug-fix", "efficient-status-tool-choice",
    "shared-root-cause-debugging", "multi-file-pi-extension-change",
    "multi-tool-orchestration", "secret-production-boundary-safety",
    "log-driven-regression-diagnosis", "subagent-delegation",
    "long-process-supervision",
}


def validate() -> None:
    manifest = json.loads((ROOT / "cases/manifest.json").read_text())
    entries = manifest["cases"]
    assert manifest["schema"] == "harnessbench.case-manifest/v1"
    assert len(entries) == 10
    assert Counter(item["difficulty"] for item in entries) == EXPECTED_DIFFICULTIES
    assert {item["category"] for item in entries} == EXPECTED_CATEGORIES
    assert len({item["id"] for item in entries}) == 10

    case_dirs = {path.name for path in (ROOT / "cases").iterdir() if path.is_dir()}
    assert case_dirs == {item["id"] for item in entries}

    for item in entries:
        case = ROOT / item["path"]
        raw = tomllib.loads((case / "task.toml").read_text())
        TaskConfig.model_validate(raw)
        assert raw["environment"]["network_mode"] == "no-network"
        assert (case / "environment/Dockerfile").is_file()
        assert (case / "instruction.md").is_file()
        assert (case / "tests/test.sh").stat().st_mode & 0o111
        assert (case / "solution/solve.sh").stat().st_mode & 0o111

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "app"
            shutil.copytree(case / "environment/app", workspace)
            env = {**os.environ, "WORKSPACE": str(workspace)}
            subprocess.run(["sh", case / "solution/solve.sh"], env=env, check=True, timeout=10)
            verified = subprocess.run(
                [sys.executable, case / "tests/verify.py"], env=env,
                text=True, capture_output=True, timeout=10,
            )
            assert verified.returncode == 0, f"{item['id']}: {verified.stdout}{verified.stderr}"

    Draft202012Validator.check_schema(json.loads((ROOT / "schemas/result.schema.json").read_text()))

    contract = tomllib.loads((ROOT / ".autoresearch/contract.toml").read_text())
    assert contract["campaign"]["default_max_experiments"] == 20
    assert contract["campaign"]["repetitions"] == 1
    assert contract["campaign"]["hard_cost_limit_usd"] == 10.0
    print("ok: 10 Harbor tasks and reference verifiers")


if __name__ == "__main__":
    validate()
