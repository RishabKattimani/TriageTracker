"""Startup diagnostics used by /health and run.sh."""

from __future__ import annotations

import importlib.util
import socket
import sys
from pathlib import Path
from typing import Any

from app import config


def python_version_ok(min_minor: int = 11) -> bool:
    return sys.version_info.major == 3 and sys.version_info.minor >= min_minor


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def asset_status(path: Path) -> dict[str, Any]:
    present = path.is_file() and path.stat().st_size > 0
    return {
        "present": present,
        "path": str(path),
        "bytes": path.stat().st_size if path.is_file() else 0,
    }


def pick_port(host: str = config.HOST, preferred: tuple[int, ...] = config.PREFERRED_PORTS) -> int:
    for port in preferred:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise RuntimeError(
        f"No available port among {list(preferred)} on {host}. "
        "Stop the process using one of those ports and retry."
    )


def collect_diagnostics(*, probe_camera: bool = False) -> dict[str, Any]:
    assets = {
        "face_landmarker_model": asset_status(config.FACE_LANDMARKER_MODEL),
        "pose_landmarker_model": asset_status(config.POSE_LANDMARKER_MODEL),
        "guided_demo_fixture": asset_status(config.GUIDED_DEMO_FIXTURE),
        "stable_fixture": asset_status(config.STABLE_FIXTURE),
    }
    packages = {
        name: module_available(name)
        for name in ("cv2", "numpy", "scipy", "fastapi", "uvicorn", "mediapipe")
    }
    camera: dict[str, Any] = {
        "available": False,
        "probed": False,
        "message": "Camera not probed at startup. Use Live Camera to test.",
    }
    if probe_camera:
        from app.video.webcam import probe_webcam

        camera = probe_webcam()
        camera["probed"] = True

    python_ok = python_version_ok()
    packages_ok = all(packages.values())
    app_ready = python_ok and packages_ok
    missing_assets = [key for key, info in assets.items() if not info["present"]]

    if app_ready and not missing_assets:
        status = "ok"
    elif app_ready:
        status = "degraded"
    else:
        status = "error"

    return {
        "status": status,
        "ready": app_ready,
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "python_version": sys.version.split()[0],
        "python_ok": python_ok,
        "packages": packages,
        "assets": assets,
        "missing_assets": missing_assets,
        "camera": camera,
        "host": config.HOST,
        "preferred_ports": list(config.PREFERRED_PORTS),
        "notes": [
            "All physiological thresholds are prototype values, not clinical.",
            "Guided Demo does not require a camera.",
            "Missing models or fixtures are reported honestly; values are never fabricated.",
        ],
    }
