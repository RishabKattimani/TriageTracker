import pytest


pytestmark = pytest.mark.milestone0


def test_health_reports_readiness_and_assets(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["status"] in {"ok", "degraded"}
    assert "assets" in payload
    for key in (
        "face_landmarker_model",
        "pose_landmarker_model",
        "guided_demo_fixture",
        "stable_fixture",
    ):
        assert key in payload["assets"]
        assert "present" in payload["assets"][key]
        assert "path" in payload["assets"][key]
    assert "camera" in payload
    assert "message" in payload["camera"]
    assert payload["python_ok"] is True
    assert payload["packages"]["fastapi"] is True
    assert payload["packages"]["cv2"] is True


def test_health_does_not_fabricate_missing_assets(client) -> None:
    payload = client.get("/health").json()
    for info in payload["assets"].values():
        if not info["present"]:
            assert info["bytes"] == 0
    assert isinstance(payload["missing_assets"], list)
