"""Waiting-room clinic: process live + controlled-change only. Backend owns state."""

from __future__ import annotations

import threading
import time
from typing import Any

import cv2
import numpy as np

from app import config
from app.models import PatientMeasurement, PatientStatus
from app.monitoring.patient import PatientMonitor
from app.signals.evm import SimpleFaceEVM
from app.video.base import CameraUnavailable, VideoSource
from app.video.file import FileVideoSource
from app.video.webcam import WebcamVideoSource
from app.vision.processor import FrameProcessor, load_fixture_meta

BACKGROUND_WAIT = {
    "P02": 18,
    "P03": 41,
    "P05": 27,
    "P06": 9,
    "P01": 6,
    "P04": 33,
}


def _static_card(patient_id: str) -> PatientMeasurement:
    return PatientMeasurement(
        patient_id=patient_id,
        timestamp=0.0,
        heart_rate=None,
        respiratory_rate=None,
        status=PatientStatus.STABLE,
        abstaining=False,
        reasons=["Simulated waiting-room tile. Not live physiology."],
    )


class Clinic:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.monitors = {pid: PatientMonitor(pid) for pid in config.PATIENT_IDS}
        self.background = {
            pid: _static_card(pid)
            for pid in config.PATIENT_IDS
            if pid not in {config.LIVE_PATIENT_ID, config.CONTROLLED_CHANGE_PATIENT_ID}
        }
        self.overlays: dict[str, np.ndarray] = {}
        self.evm_overlays: dict[str, np.ndarray] = {}
        self.evm = {config.LIVE_PATIENT_ID: SimpleFaceEVM(), config.CONTROLLED_CHANGE_PATIENT_ID: SimpleFaceEVM()}
        self.camera_error: str | None = None
        self.demo_error: str | None = None
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._live_enabled = False
        self._demo_enabled = False
        self._demo_paused = False
        self._demo_epoch = 0
        self.last_event: str | None = None

    def start(self) -> None:
        self._stop.clear()

    def stop(self) -> None:
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=2.0)
        self._threads.clear()

    def start_demo(self) -> dict[str, Any]:
        path = config.GUIDED_DEMO_FIXTURE
        if not path.is_file():
            self.demo_error = (
                f"Guided-demo fixture missing: {path}. "
                "Run: python scripts/generate_fixtures.py"
            )
            return {"ok": False, "error": self.demo_error}
        self.demo_error = None
        with self.lock:
            self.monitors[config.CONTROLLED_CHANGE_PATIENT_ID].reset()
            self._demo_paused = False
            self._demo_epoch += 1
        if not self._demo_enabled:
            self._demo_enabled = True
            thread = threading.Thread(target=self._run_file_loop, name="p04-demo", daemon=True)
            self._threads.append(thread)
            thread.start()
        return {"ok": True, "patient_id": config.CONTROLLED_CHANGE_PATIENT_ID}

    def start_live(self) -> dict[str, Any]:
        self._live_enabled = True
        if not any(t.name == "p01-live" for t in self._threads if t.is_alive()):
            thread = threading.Thread(target=self._run_live_loop, name="p01-live", daemon=True)
            self._threads.append(thread)
            thread.start()
        return {"ok": True, "patient_id": config.LIVE_PATIENT_ID}

    def set_demo_paused(self, paused: bool) -> dict[str, Any]:
        self._demo_paused = bool(paused)
        return {"ok": True, "paused": self._demo_paused}

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            patients = []
            for pid in config.PATIENT_IDS:
                if pid in self.background:
                    measurement = self.background[pid]
                    simulated = True
                else:
                    measurement = self.monitors[pid].latest
                    simulated = False
                payload = measurement.to_dict()
                payload["wait_minutes"] = BACKGROUND_WAIT.get(pid, 15)
                payload["simulated"] = simulated
                payload["processed"] = not simulated
                patients.append(payload)
            rank = {
                PatientStatus.REASSESS.value: 0,
                PatientStatus.CHANGE_DETECTED.value: 1,
                PatientStatus.SIGNAL_UNRELIABLE.value: 2,
                PatientStatus.BASELINING.value: 3,
                PatientStatus.STABLE.value: 4,
                PatientStatus.INITIALIZING.value: 5,
            }
            patients.sort(key=lambda item: (rank.get(item["status"], 9), -(item.get("change_score") or 0)))
            reassess = [p for p in patients if p["status"] == PatientStatus.REASSESS.value]
            watching = [p for p in patients if p["status"] == PatientStatus.CHANGE_DETECTED.value]
            event = self.last_event
            self.last_event = None
            return {
                "type": "snapshot",
                "waiting": len(patients),
                "reassess_count": len(reassess),
                "watching_count": len(watching),
                "patients": patients,
                "camera_error": self.camera_error,
                "demo_error": self.demo_error,
                "demo_paused": self._demo_paused,
                "thresholds": {
                    "baseline_seconds": config.BASELINE_DURATION_SECONDS,
                    "change_persistence_seconds": config.CHANGE_DETECTED_PERSISTENCE_SECONDS,
                    "reassess_persistence_seconds": config.REASSESS_PERSISTENCE_SECONDS,
                },
                "event": event,
                "note": "Backend owns patient state. Frontend must not assign REASSESS.",
            }

    def overlay_jpeg(self, patient_id: str, *, evm: bool = False) -> bytes | None:
        with self.lock:
            frame = (self.evm_overlays if evm else self.overlays).get(patient_id)
        if frame is None:
            return None
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
        if not ok:
            return None
        return encoded.tobytes()

    def _store_overlay(self, patient_id: str, obs, evm_engine: SimpleFaceEVM) -> None:
        with self.lock:
            self.overlays[patient_id] = obs.debug_overlay_frame
            self.evm_overlays[patient_id] = evm_engine.render(obs.debug_overlay_frame, obs.face_bbox)
            if self.monitors[patient_id].machine.last_event:
                self.last_event = self.monitors[patient_id].machine.last_event

    def _run_source(
        self,
        patient_id: str,
        source: VideoSource,
        processor: FrameProcessor,
        pace: bool,
        *,
        epoch: int | None = None,
    ) -> None:
        evm_engine = self.evm[patient_id]
        try:
            source.open()
            processor.open()
            last = time.time()
            for packet in source.frames():
                if self._stop.is_set():
                    break
                if epoch is not None and epoch != self._demo_epoch:
                    break
                while self._demo_paused and epoch is not None and epoch == self._demo_epoch and not self._stop.is_set():
                    time.sleep(0.08)
                if self._stop.is_set() or (epoch is not None and epoch != self._demo_epoch):
                    break
                obs = processor.process(packet)
                with self.lock:
                    measurement = self.monitors[patient_id].ingest(obs)
                self._store_overlay(patient_id, obs, evm_engine)
                _ = measurement
                if pace:
                    elapsed = time.time() - last
                    delay = max(0.0, (1.0 / config.TARGET_SAMPLE_HZ) - elapsed)
                    time.sleep(delay)
                    last = time.time()
        finally:
            processor.close()
            source.close()

    def _run_file_loop(self) -> None:
        path = config.GUIDED_DEMO_FIXTURE
        meta = load_fixture_meta(path)
        while not self._stop.is_set() and self._demo_enabled:
            epoch = self._demo_epoch
            source = FileVideoSource(path, source_id="fixture-P04", loop=False)
            processor = FrameProcessor(live=False, fixture_meta=meta)
            self._run_source(
                config.CONTROLLED_CHANGE_PATIENT_ID,
                source,
                processor,
                pace=True,
                epoch=epoch,
            )
            time.sleep(0.4)

    def _run_live_loop(self) -> None:
        while not self._stop.is_set() and self._live_enabled:
            source = WebcamVideoSource(source_id="webcam-P01")
            processor = FrameProcessor(live=True)
            try:
                self.camera_error = None
                self._run_source(config.LIVE_PATIENT_ID, source, processor, pace=False)
            except CameraUnavailable as exc:
                self.camera_error = str(exc)
                time.sleep(2.0)
            except Exception as exc:
                self.camera_error = f"Live camera stopped: {exc}"
                time.sleep(2.0)


clinic = Clinic()
