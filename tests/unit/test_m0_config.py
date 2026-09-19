import inspect

import pytest

from app import config


pytestmark = pytest.mark.milestone0


def test_prototype_thresholds_live_in_config_not_magic_inline() -> None:
    source = inspect.getsource(config)
    assert "PROTOTYPE" in source or "prototype" in source
    assert config.PULSE_BAND_HZ == (0.7, 3.0)
    assert config.RESP_BAND_HZ == (0.1, 0.7)
    assert config.BASELINE_DURATION_SECONDS >= 20
    assert config.BASELINE_DURATION_SECONDS <= 30


def test_repeatability_tolerances_are_predeclared() -> None:
    assert config.REPEATABILITY_HR_TOLERANCE_BPM == 8.0
    assert config.REPEATABILITY_RR_TOLERANCE_BRPM == 4.0
    assert config.REPEATABILITY_CONFIDENCE_TOLERANCE == 0.15


def test_required_and_prohibited_wording() -> None:
    assert "Physiological change detected." in config.REQUIRED_WORDING_CHANGE
    assert "Reassessment recommended." in config.REQUIRED_WORDING_REASSESS
    assert "sepsis" not in config.REQUIRED_WORDING_CHANGE.lower()
    assert any("sepsis" in item.lower() for item in config.PROHIBITED_WORDING)


def test_preferred_ports_are_documented_and_local() -> None:
    assert config.HOST == "127.0.0.1"
    assert 8765 in config.PREFERRED_PORTS
    assert config.DEFAULT_PORT in config.PREFERRED_PORTS
