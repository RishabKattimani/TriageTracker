"""Patient state machine. SIGNAL_UNRELIABLE is display-only and never an alert."""

from __future__ import annotations

from app import config
from app.models import PatientStatus


class PatientStateMachine:
    def __init__(self) -> None:
        self.trustworthy = PatientStatus.INITIALIZING
        self.persistence = 0.0
        self._below_since: float | None = None
        self.last_event: str | None = None

    def reset(self) -> None:
        self.trustworthy = PatientStatus.INITIALIZING
        self.persistence = 0.0
        self._below_since = None
        self.last_event = None

    def display_status(self, abstaining: bool) -> PatientStatus:
        if abstaining:
            return PatientStatus.SIGNAL_UNRELIABLE
        return self.trustworthy

    def update(
        self,
        *,
        timestamp: float,
        dt: float,
        baseline_ready: bool,
        change_score: float | None,
        abstaining: bool,
        recovered: bool,
    ) -> PatientStatus:
        self.last_event = None
        if recovered:
            self.last_event = config.REQUIRED_WORDING_REACQUIRED
        if abstaining or change_score is None:
            if dt > 0 and self._below_since is None:
                self._below_since = timestamp
            return self.display_status(abstaining)

        if not baseline_ready:
            self.trustworthy = PatientStatus.BASELINING
            self.persistence = 0.0
            return self.trustworthy

        if change_score >= config.CHANGE_DETECTED_SCORE:
            self.persistence += max(dt, 0.0)
            self._below_since = None
        else:
            if self._below_since is None:
                self._below_since = timestamp
            elif timestamp - self._below_since >= config.SPIKE_RESET_SECONDS:
                self.persistence = 0.0
            if self.trustworthy == PatientStatus.REASSESS:
                return self.trustworthy
            if self.trustworthy == PatientStatus.CHANGE_DETECTED and self.persistence > 0:
                return self.trustworthy
            self.trustworthy = PatientStatus.STABLE
            return self.trustworthy

        if (
            change_score >= config.REASSESS_SCORE
            and self.persistence >= config.REASSESS_PERSISTENCE_SECONDS
        ):
            self.trustworthy = PatientStatus.REASSESS
        elif (
            change_score >= config.CHANGE_DETECTED_SCORE
            and self.persistence >= config.CHANGE_DETECTED_PERSISTENCE_SECONDS
        ):
            if self.trustworthy != PatientStatus.REASSESS:
                self.trustworthy = PatientStatus.CHANGE_DETECTED
        elif self.trustworthy not in (PatientStatus.CHANGE_DETECTED, PatientStatus.REASSESS):
            self.trustworthy = PatientStatus.STABLE

        return self.display_status(False)
