from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_examples_runner_skips_optional_rayx_and_reports_timeout(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    source_script = repo_root / "examples" / "run_all_examples.sh"

    fake_repo = tmp_path / "repo"
    fake_examples = fake_repo / "examples"
    fake_examples.mkdir(parents=True)
    (fake_repo / ".venv" / "bin").mkdir(parents=True)

    shutil.copy2(source_script, fake_examples / "run_all_examples.sh")
    (fake_repo / ".venv" / "bin" / "activate").write_text("", encoding="utf-8")
    os.symlink(sys.executable, fake_repo / ".venv" / "bin" / "python")

    (fake_examples / "pass_case").mkdir()
    (fake_examples / "pass_case" / "plain_demo.py").write_text("print('ok')\n", encoding="utf-8")

    (fake_examples / "timeout_case").mkdir()
    (fake_examples / "timeout_case" / "plain_timeout.py").write_text(
        "import time\ntime.sleep(2)\n",
        encoding="utf-8",
    )

    (fake_examples / "rayx_case").mkdir()
    (fake_examples / "rayx_case" / "simulation_rayx_demo.py").write_text(
        "from raypyng import Simulate\nsim = Simulate('dummy', engine='rayx')\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [
            str(fake_repo / ".venv" / "bin"),
            str(Path(sys.executable).resolve().parent),
            env.get("PATH", ""),
        ]
    )

    result = subprocess.run(
        ["bash", str(fake_examples / "run_all_examples.sh"), "--demo", "--simulation", "--timeout", "1"],
        cwd=fake_repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "TIMED OUT after 1s" in result.stdout
    assert "SKIPPED" in result.stdout
    assert "requires optional rayx support" in result.stdout
    assert "Skipped: 1" in result.stdout
