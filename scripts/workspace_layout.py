from pathlib import Path
import shutil


def prepare_workspace(case: Path, root: Path, auth: Path):
    workspace = root / "workspace" / "app"
    control = root / "control"
    agent = control / "agent"
    sessions = control / "sessions"
    workspace.parent.mkdir()
    agent.mkdir(parents=True)
    sessions.mkdir()
    shutil.copytree(case / "environment/app", workspace)
    (agent / "auth.json").symlink_to(auth)
    return workspace, agent, sessions
