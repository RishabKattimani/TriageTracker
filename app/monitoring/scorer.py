"""Transparent weighted change scorer. Prototype thresholds only."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app import config
from app.models import ChangeScoreResult, FeatureVector


class ChangeScorer(ABC):
    @abstractmethod
    def score(self, features: FeatureVector) -> ChangeScoreResult:
        raise NotImplementedError


class WeightedRuleChangeScorer(ChangeScorer):
    def score(self, features: FeatureVector) -> ChangeScoreResult:
        hr_ok = (
            features.hr_delta_pct is not None
            and features.hr_confidence >= config.HR_CONFIDENCE_THRESHOLD
        )
        rr_ok = (
            features.rr_delta_pct is not None
            and features.rr_confidence >= config.RR_CONFIDENCE_THRESHOLD
        )
        if not hr_ok and not rr_ok:
            return ChangeScoreResult(score=None, reasons=[], contributing=False)

        parts: list[tuple[float, float]] = []
        reasons: list[str] = []

        if hr_ok:
            mag = min(1.0, abs(features.hr_delta_pct or 0.0) / 0.25)
            parts.append((config.WEIGHT_HR_DELTA, mag * features.hr_confidence))
            pct = (features.hr_delta_pct or 0.0) * 100.0
            sign = "+" if pct >= 0 else ""
            reasons.append(f"Heart rate {sign}{pct:.0f}% from baseline")
            if features.hr_slope is not None:
                slope_mag = min(1.0, abs(features.hr_slope) / 2.0)
                parts.append((config.WEIGHT_HR_SLOPE, slope_mag * features.hr_confidence))

        if rr_ok:
            mag = min(1.0, abs(features.rr_delta_pct or 0.0) / 0.25)
            parts.append((config.WEIGHT_RR_DELTA, mag * features.rr_confidence))
            pct = (features.rr_delta_pct or 0.0) * 100.0
            sign = "+" if pct >= 0 else ""
            reasons.append(f"Respiratory rate {sign}{pct:.0f}% from baseline")

        # Persistence is a state-machine gate, not a score prerequisite.
        # Including it in the score created a circular stall: persist=0 kept
        # the score below the threshold that would start persistence.
        if features.persistence_seconds > 0:
            reasons.append(f"Change persisted for {features.persistence_seconds:.0f} seconds")

        if features.hr_confidence >= 0.7:
            reasons.append("Signal confidence high")
        if features.roi_agreement >= config.ROI_AGREEMENT_THRESHOLD:
            reasons.append(f"ROI agreement {features.roi_agreement:.2f}")
        if features.motion_score < config.MOTION_ABSTAIN_THRESHOLD:
            reasons.append("Motion quality acceptable")

        weight_sum = sum(w for w, _ in parts)
        if weight_sum <= 0:
            return ChangeScoreResult(score=None, reasons=[], contributing=False)
        score = sum(w * term for w, term in parts) / weight_sum
        return ChangeScoreResult(score=float(min(1.0, score)), reasons=reasons, contributing=True)
