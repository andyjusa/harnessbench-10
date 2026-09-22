"""Managed-Pi Harbor adapters configured only by environment variables."""
from __future__ import annotations

import json
import shlex

from harbor.agents.installed.base import BaseInstalledAgent, with_prompt_template
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class ManagedPi(BaseInstalledAgent):
    ptc = False

    @staticmethod
    def name() -> str:
        return "managed-pi"

    async def install(self, environment: BaseEnvironment) -> None:
        artifact = self._get_env("HARNESSBENCH_PI_ARTIFACT")
        if not artifact:
            raise ValueError("HARNESSBENCH_PI_ARTIFACT must name a mounted public build artifact")
        await self.exec_as_root(environment, f"test -e {shlex.quote(artifact)}")

    @with_prompt_template
    async def run(self, instruction: str, environment: BaseEnvironment, context: AgentContext) -> None:
        command = self._get_env("HARNESSBENCH_PI_COMMAND")
        if not command:
            raise ValueError("HARNESSBENCH_PI_COMMAND is required")
        args = json.loads(self._get_env("HARNESSBENCH_PI_ARGS_JSON") or "[]")
        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            raise ValueError("HARNESSBENCH_PI_ARGS_JSON must be a JSON string array")
        await self.exec_as_agent(
            environment,
            " ".join(map(shlex.quote, [command, *args, instruction])),
            env={"PI_PTC": "1" if self.ptc else "0"},
        )


class ManagedPiPtcOn(ManagedPi):
    ptc = True

    @staticmethod
    def name() -> str:
        return "managed-pi-ptc-on"


class ManagedPiPtcOff(ManagedPi):
    @staticmethod
    def name() -> str:
        return "managed-pi-ptc-off"
