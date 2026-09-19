from pathlib import Path

import pytest


pytestmark = pytest.mark.milestone0

ROOT = Path(__file__).resolve().parents[2]
RUN_SH = ROOT / "run.sh"
README = ROOT / "README.md"


def test_run_sh_exists_and_is_executable() -> None:
    assert RUN_SH.is_file()
    assert RUN_SH.stat().st_mode & 0o111


def test_run_sh_covers_required_launch_steps() -> None:
    text = RUN_SH.read_text(encoding="utf-8")
    required_fragments = [
        "3.11",
        ".venv",
        "requirements.txt",
        "/health",
        "open ",
        "trap",
        "TRIAGETRACKER_SKIP_BROWSER",
    ]
    missing = [item for item in required_fragments if item not in text]
    assert missing == []


def test_readme_quick_start_is_run_sh_only() -> None:
    text = README.read_text(encoding="utf-8")
    assert "./run.sh" in text
    assert "Quick start" in text or "quick start" in text.lower()
    lowered = text.lower()
    assert "docker compose" not in lowered
    assert "docker-compose" not in lowered
    assert "npm install" not in lowered
    assert "the only required launch command" in lowered
