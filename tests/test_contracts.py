from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from harnessbench.agents import ManagedPiPtcOff, ManagedPiPtcOn
from harnessbench.results import load_result


class FakeEnvironment:
    def __init__(self):
        self.calls = []

    async def exec(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(return_code=0, stdout="", stderr="")


class AdapterTests(unittest.TestCase):
    def test_variants_set_only_the_ptc_value(self):
        for cls, expected in ((ManagedPiPtcOn, "1"), (ManagedPiPtcOff, "0")):
            environment = FakeEnvironment()
            with tempfile.TemporaryDirectory() as directory, patch.dict(
                "os.environ",
                {
                    "HARNESSBENCH_PI_ARTIFACT": "/mounted/pi",
                    "HARNESSBENCH_PI_COMMAND": "/mounted/pi",
                    "HARNESSBENCH_PI_ARGS_JSON": '["--model", "codex-fixed"]',
                },
                clear=False,
            ):
                agent = cls(logs_dir=Path(directory))
                asyncio.run(agent.run("do work", environment, None))
            call = environment.calls[-1]
            self.assertEqual(call["env"], {"PI_PTC": expected})
            self.assertTrue(call["command"].endswith("/mounted/pi --model codex-fixed 'do work'"))

    def test_rejects_non_string_arguments(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            "os.environ",
            {"HARNESSBENCH_PI_COMMAND": "pi", "HARNESSBENCH_PI_ARGS_JSON": "[1]"},
            clear=False,
        ):
            agent = ManagedPiPtcOn(logs_dir=Path(directory))
            with self.assertRaises(ValueError):
                asyncio.run(agent.run("work", FakeEnvironment(), None))


class ResultTests(unittest.TestCase):
    def test_correctness_is_verifier_gate(self):
        result = {
            "schema": "harnessbench.result/v1", "case_id": "01", "variant": "ptc-on",
            "correct": True, "verifier_result": 1, "wall_time_seconds": 1.0,
            "model_turns": 1, "backend_calls": 1, "input_tokens": 1,
            "output_tokens": 1, "cache_read_tokens": 0, "cache_write_tokens": 0,
            "cost_usd": 0.01, "tool_calls": 1, "retries": 0, "timeouts": 0,
            "failures": [],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json") as file:
            json.dump(result, file); file.flush()
            self.assertTrue(load_result(file.name)["accepted"])
            result["correct"] = False
            file.seek(0); file.truncate(); json.dump(result, file); file.flush()
            with self.assertRaises(ValueError):
                load_result(file.name)


if __name__ == "__main__":
    unittest.main()
