/* Frontend renders backend state. It must never assign REASSESS or invent HR/RR. */
(function () {
  const status = document.createElement("div");
  status.id = "backend-connection";
  status.hidden = true;
  document.body.appendChild(status);

  function show(message, kind) {
    status.hidden = false;
    status.className = "notice " + (kind || "");
    status.textContent = message;
  }

  const path = window.location.pathname;
  let selectedId = path === "/live" ? "P01" : "P04";
  let evm = false;
  let lastAlert = null;
  let demoPaused = false;
  let demoStage = 0;
  const demoLines = [
    "Stage 1 / 5 — Six-patient waiting room. Only P01 (live) and P04 (fixture) are processed.",
    "Stage 2 / 5 — The fixture uses the same FramePacket path as the webcam. No camera needed.",
    "Stage 3 / 5 — Still, high-quality signal can produce HR. Motion forces abstention.",
    "Stage 4 / 5 — A personal baseline is collected, then only a sustained valid change can alert.",
    "Stage 5 / 5 — If flagged, the backend moves that patient to the top and explains why.",
  ];

  function fmt(value, suffix) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") return value.toFixed(1) + (suffix || "");
    return String(value);
  }

  function rrLabel(patient) {
    if (patient.respiratory_rate === null || patient.respiratory_rate === undefined) {
      return "RR unavailable — insufficient signal quality.";
    }
    return fmt(patient.respiratory_rate, " brpm");
  }

  function renderBoard(snapshot) {
    const board = document.getElementById("patient-board");
    if (!board) return;
    board.innerHTML = "";
    snapshot.patients.forEach(function (patient) {
      const card = document.createElement("article");
      card.className = "card " + patient.status;
      card.dataset.patientId = patient.patient_id;
      card.innerHTML =
        "<h3>" + patient.patient_id + ' <span class="badge ' + patient.status + '">' + patient.status + "</span></h3>" +
        '<p class="muted">Wait ' + patient.wait_minutes + " min" + (patient.simulated ? " · simulated tile" : " · processed") + "</p>" +
        "<p>HR " + (patient.heart_rate === null ? "—" : Math.round(patient.heart_rate) + " bpm") + "</p>" +
        "<p>" + rrLabel(patient) + "</p>" +
        "<p>Confidence " + fmt(patient.heart_rate_confidence) + "</p>";
      card.addEventListener("click", function () {
        if (patient.processed) selectedId = patient.patient_id;
        updateVideo();
        renderDetail(patient);
      });
      board.appendChild(card);
    });
    const counts = document.getElementById("room-counts");
    if (counts) {
      counts.textContent = snapshot.waiting + " waiting · " + snapshot.reassess_count + " requiring reassessment";
    }
  }

  function renderDetail(patient) {
    if (!patient) return;
    const title = document.getElementById("detail-title");
    const metrics = document.getElementById("detail-metrics");
    const why = document.getElementById("why-flagged");
    if (title) title.textContent = patient.patient_id + " — " + patient.status;
    if (metrics) {
      metrics.innerHTML =
        "<dt>HR</dt><dd>" + (patient.heart_rate === null ? "Signal unreliable" : Math.round(patient.heart_rate) + " bpm") + "</dd>" +
        "<dt>RR</dt><dd>" + rrLabel(patient) + "</dd>" +
        "<dt>Confidence</dt><dd>" + fmt(patient.heart_rate_confidence) + "</dd>" +
        "<dt>Motion</dt><dd>" + fmt(patient.motion_score) + "</dd>" +
        "<dt>Baseline HR</dt><dd>" + fmt(patient.baseline_heart_rate, " bpm") + "</dd>" +
        "<dt>HR delta</dt><dd>" + (patient.heart_rate_delta_pct === null ? "—" : (patient.heart_rate_delta_pct * 100).toFixed(0) + "%") + "</dd>" +
        "<dt>Persistence</dt><dd>" + fmt(patient.persistence_seconds, " s") + "</dd>" +
        "<dt>Change score</dt><dd>" + fmt(patient.change_score) + "</dd>";
    }
    if (why) {
      why.innerHTML = "";
      const reasons = patient.reasons && patient.reasons.length ? patient.reasons : ["No alert reasons from backend."];
      reasons.forEach(function (reason) {
        const li = document.createElement("li");
        li.textContent = reason;
        why.appendChild(li);
      });
    }
  }

  function updateVideo() {
    const img = document.getElementById("patient-video");
    if (!img) return;
    img.src = "/stream/" + selectedId + (evm ? "?evm=true" : "") + "&t=" + Date.now();
  }

  function maybePopup(snapshot) {
    const popup = document.getElementById("reassess-popup");
    if (!popup) return;
    const flagged = snapshot.patients.find(function (p) { return p.status === "REASSESS"; });
    if (flagged && flagged.patient_id !== lastAlert) {
      lastAlert = flagged.patient_id;
      popup.hidden = false;
      popup.textContent = "Patient " + flagged.patient_id +
        " has shown a sustained physiological deviation from baseline. Reassessment recommended.";
    }
    const eventBox = document.getElementById("signal-event");
    if (eventBox && snapshot.event) {
      eventBox.hidden = false;
      eventBox.textContent = snapshot.event;
    }
    const cam = document.getElementById("camera-error");
    if (cam && snapshot.camera_error) {
      cam.hidden = false;
      cam.textContent = snapshot.camera_error;
    }
  }

  function applySnapshot(snapshot) {
    if (!snapshot || snapshot.type !== "snapshot") return;
    renderBoard(snapshot);
    const selected = snapshot.patients.find(function (p) { return p.patient_id === selectedId; });
    renderDetail(selected || snapshot.patients[0]);
    maybePopup(snapshot);
  }

  function connect() {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(proto + "://" + window.location.host + "/ws/telemetry");
    socket.addEventListener("open", function () { status.hidden = true; });
    socket.addEventListener("message", function (event) {
      const data = JSON.parse(event.data);
      applySnapshot(data);
    });
    socket.addEventListener("close", function () {
      show("Backend disconnected. Reconnecting… Measurements are not live.", "warn");
      window.setTimeout(connect, 1500);
    });
  }

  function postStart(mode) {
    fetch("/api/session/start?mode=" + mode, { method: "POST" })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data.ok && data.error) show(data.error, "warn");
      })
      .catch(function () { show("Could not start session. Is the server running?", "warn"); });
  }

  const raw = document.getElementById("btn-raw");
  const evmBtn = document.getElementById("btn-evm");
  if (raw) raw.addEventListener("click", function () { evm = false; updateVideo(); });
  if (evmBtn) evmBtn.addEventListener("click", function () { evm = true; updateVideo(); });

  if (path === "/demo") {
    postStart("demo");
    const start = document.getElementById("demo-start");
    const pause = document.getElementById("demo-pause");
    const skip = document.getElementById("demo-skip");
    const copy = document.getElementById("demo-copy");
    const stage = document.getElementById("demo-stage");
    function showStage() {
      if (copy) copy.textContent = demoLines[demoStage];
      if (stage) stage.textContent = "Stage " + (demoStage + 1) + " / 5";
    }
    showStage();
    if (start) start.addEventListener("click", function () {
      lastAlert = null;
      demoStage = 0;
      demoPaused = false;
      showStage();
      postStart("demo");
    });
    if (pause) pause.addEventListener("click", function () { demoPaused = !demoPaused; });
    if (skip) skip.addEventListener("click", function () { demoStage = demoLines.length - 1; showStage(); });
    window.setInterval(function () {
      if (!demoPaused && demoStage < demoLines.length - 1) {
        demoStage += 1;
        showStage();
      }
    }, 12000);
  }
  if (path === "/live") {
    const live = document.getElementById("live-start");
    if (live) live.addEventListener("click", function () { postStart("live"); });
  }
  if (path === "/dashboard") {
    postStart("demo");
  }

  if (path !== "/health") connect();
})();
