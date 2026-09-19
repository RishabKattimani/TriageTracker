"""HTTP and WebSocket routes. Frontend renders backend state only."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from app import config
from app.clinic import clinic
from app.diagnostics import collect_diagnostics

router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))


def _page(request: Request, name: str) -> HTMLResponse:
    diagnostics = collect_diagnostics(probe_camera=False)
    return templates.TemplateResponse(
        request,
        name,
        {"request": request, "diagnostics": diagnostics, "config": config},
    )


@router.get("/health")
def health(probe_camera: bool = False) -> dict:
    payload = collect_diagnostics(probe_camera=probe_camera)
    payload["clinic"] = {
        "live_patient": config.LIVE_PATIENT_ID,
        "controlled_change_patient": config.CONTROLLED_CHANGE_PATIENT_ID,
    }
    return payload


@router.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return _page(request, "home.html")


@router.get("/demo", response_class=HTMLResponse)
def guided_demo(request: Request) -> HTMLResponse:
    return _page(request, "demo.html")


@router.get("/live", response_class=HTMLResponse)
def live_camera(request: Request) -> HTMLResponse:
    return _page(request, "live.html")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    return _page(request, "dashboard.html")


@router.get("/api/patients")
def patients() -> dict:
    return clinic.snapshot()


@router.post("/api/session/start")
def start_session(mode: str = Query(..., pattern="^(demo|live)$")) -> JSONResponse:
    if mode == "demo":
        result = clinic.start_demo()
    else:
        result = clinic.start_live()
    status = 200 if result.get("ok") else 409
    return JSONResponse(result, status_code=status)


@router.get("/stream/{patient_id}")
def stream(patient_id: str, evm: bool = False) -> StreamingResponse:
    def frames():
        while True:
            jpeg = clinic.overlay_jpeg(patient_id, evm=evm)
            if jpeg is None:
                blank = _blank_jpeg()
                jpeg = blank
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            time.sleep(0.08)

    return StreamingResponse(frames(), media_type="multipart/x-mixed-replace; boundary=frame")


@router.websocket("/ws/telemetry")
async def telemetry(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        await websocket.send_json(
            {
                "type": "hello",
                "version": config.APP_VERSION,
                "note": "Backend owns patient state. Frontend must not assign REASSESS.",
            }
        )
        while True:
            await websocket.send_json(clinic.snapshot())
            await asyncio.sleep(0.35)
    except WebSocketDisconnect:
        return


def _blank_jpeg() -> bytes:
    import cv2
    import numpy as np

    frame = np.full((180, 320, 3), 40, dtype=np.uint8)
    cv2.putText(frame, "Waiting for video", (24, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220, 220, 220), 1)
    ok, encoded = cv2.imencode(".jpg", frame)
    return encoded.tobytes() if ok else b""
