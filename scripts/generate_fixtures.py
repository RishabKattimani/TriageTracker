#!/usr/bin/env python3
"""Generate synthetic optical fixtures used by Guided Demo and tests."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.synth import generate_repo_fixtures  # noqa: E402


def main() -> None:
    paths = generate_repo_fixtures(ROOT / "fixtures")
    for name, path in paths.items():
        print(f"{name}: {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
