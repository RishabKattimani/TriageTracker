"""Shared video input contract.

Physiology code must consume FramePacket only. It must not open cv2.VideoCapture.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterator

from app.models import FramePacket

__all__ = ["CameraUnavailable", "FramePacket", "VideoSource"]


class CameraUnavailable(RuntimeError):
    """Webcam could not be opened. Message is safe to show in the UI."""


class VideoSource(ABC):
    """Single input interface for webcam and file video."""

    @property
    @abstractmethod
    def source_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def open(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self) -> FramePacket | None:
        """Return the next FramePacket, or None at end-of-stream."""
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def is_open(self) -> bool:
        raise NotImplementedError

    def frames(self) -> Iterator[FramePacket]:
        while True:
            packet = self.read()
            if packet is None:
                break
            yield packet

    def __enter__(self) -> "VideoSource":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
