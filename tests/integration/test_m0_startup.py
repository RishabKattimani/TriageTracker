import pytest


pytestmark = pytest.mark.milestone0


def test_homepage_explains_problem_use_case_and_actions(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "Triage is a snapshot. Patients keep changing." in body
    assert "ordinary-camera" in body.lower() or "Ordinary-camera" in body
    assert "RUN GUIDED DEMO" in body
    assert "TRY LIVE CAMERA" in body
    assert "Decision support only" in body
    assert "What is real vs simulated?" in body
    assert "startup-diagnostics" in body


def test_demo_and_live_routes_do_not_require_camera(client) -> None:
    demo = client.get("/demo")
    live = client.get("/live")
    assert demo.status_code == 200
    assert live.status_code == 200
    assert "REASSESS" in demo.text
    assert "cannot assign REASSESS" in demo.text
    assert "Guided Demo remains available" in live.text


def test_websocket_hello_states_backend_owns_alerts(client) -> None:
    with client.websocket_connect("/ws/telemetry") as socket:
        message = socket.receive_json()
    assert message["type"] == "hello"
    assert "REASSESS" in message["note"]
