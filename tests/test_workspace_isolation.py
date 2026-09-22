from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from workspace_layout import prepare_workspace


class WorkspaceIsolationTests(unittest.TestCase):
    def test_control_state_is_not_under_workspace_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            case = root / "case"
            (case / "environment/app").mkdir(parents=True)
            (case / "environment/app/example.py").write_text("pass\n")
            auth = root / "auth.json"
            auth.write_text("{}\n")
            run_root = root / "run"
            run_root.mkdir()
            workspace, agent, sessions = prepare_workspace(case, run_root, auth)
            self.assertEqual(workspace.parent, run_root / "workspace")
            self.assertEqual(agent.parent, run_root / "control")
            self.assertEqual(sessions.parent, run_root / "control")
            self.assertFalse(agent.is_relative_to(workspace.parent))
            self.assertEqual((workspace / "example.py").read_text(), "pass\n")


if __name__ == "__main__":
    unittest.main()
