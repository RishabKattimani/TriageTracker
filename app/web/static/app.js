/* Frontend renders backend state. It must never assign REASSESS or invent HR/RR. */
(function () {
  const status = document.createElement("div");
  status.id = "backend-connection";
  status.hidden = true;
  document.body.appendChild(status);

  const STATUS_LABEL = {
    INITIALIZING: "Initializing",
    BASELINING: "Collecting baseline",
    STABLE: "Stable",
    CHANGE_DETECTED: "Physiological change detected.",
    REASSESS: "Reassessment recommended.",
    SIGNAL_UNRELIABLE: "Signal unreliable — no inference made.",
  };

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
  let connected = false;
  const demoLines = [
    "Stage 1 / 9 — Triage is a snapshot. These six cards are a waiting room, not a diagnosis.",
    "Stage 2 / 9 — P01 is the live slot. P04 is the controlled-change fixture. Four tiles are simulated context.",
    "Stage 3 / 9 — RAW shows facial ROIs. EVM is visualization only; HR still comes from the backend rPPG contract.",
    "Stage 4 / 9 — Motion or a missing face must show Signal unreliable — no inference made. That is not an alert.",
    "Stage 5 / 9 — Guided Demo plays the controlled-change MP4 through the same Core path as the webcam.",
    "Stage 6 / 9 — Watch backend status move: INITIALIZING → BASELINING → STABLE. The UI does not set these.",
    "Stage 7 / 9 — A patient rises to the top only after the backend emits REASSESS. No button can force that.",
    "Stage 8 / 9 — Why flagged lists backend reasons: deviation, persistence, confidence, ROI agreement, motion.",
    "Stage 9 / 9 — Decision support only. It does not diagnose or replace triage. Try Live Camera when ready.",
  ];

  function safe(patient, key, fallback) {
    if (!patient || patient[key] === undefined) return fallback;
    return patient[key];
  }

  function fmt(value, suffix) {
    if (value === null || value === undefined) return "—";
    if (typeof value === "number") return value.toFixed(1) + (suffix || "");
    return String(value);
  }

  function rrLabel(patient) {
    if (!patient || patient.respiratory_rate === null || patient.respiratory_rate === undefined) {
      return "RR unavailable — insufficient signal quality.";
    }
    return fmt(patient.respiratory_rate, " brpm");
  }

  function hrLabel(patient) {
    if (!connected) return "Not live — backend disconnected.";
    if (!patient) return "—";
    if (patient.abstaining || patient.status === "SIGNAL_UNRELIABLE" || patient.heart_rate === null) {
      return "Signal unreliable — no inference made.";
    }
    return Math.round(patient.heart_rate) + " bpm";
  }

  function statusText(code) {
    return STATUS_LABEL[code] || code || "INITIALIZING";
  }

  function renderBoard(snapshot) {
    const board = document.getElementById("patient-board");
    if (!board) return;
    board.innerHTML = "";
    (snapshot.patients || []).forEach(function (patient) {
      const card = document.createElement("article");
      const code = safe(patient, "status", "INITIALIZING");
      card.className = "card " + code;
      card.dataset.patientId = safe(patient, "patient_id", "");
      const simulated = !!patient.simulated;
      card.innerHTML =
        "<h3>" + safe(patient, "patient_id", "?") +
        ' <span class="badge ' + code + '">' + statusText(code) + "</span></h3>" +
        '<p class="muted">Wait ' + safe(patient, "wait_minutes", "—") + " min" +
        (simulated ? " · simulated tile — not live physiology" : " · processed") + "</p>" +
        "<p>HR " + (simulated ? "—" : hrLabel(patient)) + "</p>" +
        "<p>" + (simulated ? "RR unavailable — insufficient signal quality." : rrLabel(patient)) + "</p>" +
        "<p>Confidence " + (simulated ? "—" : fmt(patient.heart_rate_confidence)) + "</p>";
      card.addEventListener("click", function () {
        if (patient.processed) selectedId = patient.patient_id;
        updateVideo();
        renderDetail(patient);
      });
      board.appendChild(card);
    });
    const counts = document.getElementById("room-counts");
    if (counts) {
      counts.textContent = safe(snapshot, "waiting", 0) + " waiting · " +
        safe(snapshot, "reassess_count", 0) + " requiring reassessment";
    }
  }

  function renderDetail(patient) {
    if (!patient) return;
    const title = document.getElementById("detail-title");
    const metrics = document.getElementById("detail-metrics");
    const why = document.getElementById("why-flagged");
    const proof = document.getElementById("tech-proof");
    const code = safe(patient, "status", "INITIALIZING");
    if (title) title.textContent = safe(patient, "patient_id", "") + " — " + statusText(code);
    if (metrics) {
      const liveHr = hrLabel(patient);
      metrics.innerHTML =
        "<dt>HR</dt><dd>" + liveHr + "</dd>" +
        "<dt>RR</dt><dd>" + rrLabel(patient) + "</dd>" +
        "<dt>Confidence</dt><dd>" + fmt(patient.heart_rate_confidence) + "</dd>" +
        "<dt>Motion</dt><dd>" + fmt(patient.motion_score) + "</dd>" +
        "<dt>Baseline HR</dt><dd>" + fmt(patient.baseline_heart_rate, " bpm") + "</dd>" +
        "<dt>Baseline RR</dt><dd>" + fmt(patient.baseline_respiratory_rate, " brpm") + "</dd>" +
        "<dt>HR delta</dt><dd>" + (patient.heart_rate_delta_pct === null || patient.heart_rate_delta_pct === undefined ? "—" : (patient.heart_rate_delta_pct * 100).toFixed(0) + "%") + "</dd>" +
        "<dt>Persistence</dt><dd>" + fmt(patient.persistence_seconds, " s") + "</dd>";
    }
    if (why) {
      why.innerHTML = "";
      let reasons = patient.reasons && patient.reasons.length ? patient.reasons.slice() : [];
      if (patient.abstaining || code === "SIGNAL_UNRELIABLE") {
        if (reasons.indexOf("Signal unreliable — no inference made.") === -1) {
          reasons.unshift("Signal unreliable — no inference made.");
        }
        if (patient.abstention_reason) reasons.push(patient.abstention_reason);
      }
      if (!reasons.length) reasons = ["No alert reasons from backend."];
      reasons.forEach(function (reason) {
        const li = document.createElement("li");
        li.textContent = reason;
        why.appendChild(li);
      });
    }
    if (proof) {
      proof.innerHTML =
        "<dt>Status</dt><dd>" + code + "</dd>" +
        "<dt>Change score</dt><dd>" + fmt(patient.change_score) + "</dd>" +
        "<dt>ROI agreement</dt><dd>" + fmt(patient.roi_agreement) + "</dd>" +
        "<dt>Signal quality</dt><dd>" + fmt(patient.signal_quality) + "</dd>" +
        "<dt>Abstaining</dt><dd>" + String(!!patient.abstaining) + "</dd>" +
        "<dt>Abstention reason</dt><dd>" + (patient.abstention_reason || "—") + "</dd>" +
        "<dt>Processed</dt><dd>" + String(!!patient.processed) + "</dd>";
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
    const flagged = (snapshot.patients || []).find(function (p) { return p.status === "REASSESS"; });
    if (flagged && flagged.patient_id !== lastAlert) {
      lastAlert = flagged.patient_id;
      popup.hidden = false;
      popup.textContent = "Patient " + flagged.patient_id +
        " has shown a sustained physiological deviation from baseline. Reassessment recommended.";
    }
    if (!flagged) popup.hidden = true;
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
    const selected = (snapshot.patients || []).find(function (p) { return p.patient_id === selectedId; });
    renderDetail(selected || (snapshot.patients || [])[0]);
    maybePopup(snapshot);
    if (path === "/demo") maybeAdvanceFromBackend(snapshot);
  }

  function maybeAdvanceFromBackend(snapshot) {
    const p04 = (snapshot.patients || []).find(function (p) { return p.patient_id === "P04"; });
    if (!p04 || demoPaused) return;
    if (p04.status === "REASSESS" && demoStage < 7) {
      demoStage = 7;
      showStage();
    }
  }

  function connect() {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(proto + "://" + window.location.host + "/ws/telemetry");
    socket.addEventListener("open", function () {
      connected = true;
      status.hidden = true;
    });
    socket.addEventListener("message", function (event) {
      let data;
      try { data = JSON.parse(event.data); } catch (err) { return; }
      applySnapshot(data);
    });
    socket.addEventListener("close", function () {
      connected = false;
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

  function resetDemo() {
    lastAlert = null;
    demoStage = 0;
    demoPaused = false;
    const popup = document.getElementById("reassess-popup");
    if (popup) popup.hidden = true;
    showStage();
    fetch("/api/session/reset", { method: "POST" })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data.ok && data.error) show(data.error, "warn");
      })
      .catch(function () { show("Reset failed. Is the server running?", "warn"); });
  }

  function showStage() {
    const copy = document.getElementById("demo-copy");
    const stage = document.getElementById("demo-stage");
    if (copy) copy.textContent = demoLines[demoStage];
    if (stage) stage.textContent = "Stage " + (demoStage + 1) + " / 9";
  }

  const raw = document.getElementById("btn-raw");
  const evmBtn = document.getElementById("btn-evm");
  if (raw) raw.addEventListener("click", function () { evm = false; updateVideo(); });
  if (evmBtn) evmBtn.addEventListener("click", function () { evm = true; updateVideo(); });

  if (path === "/demo") {
    postStart("demo");
    showStage();
    const start = document.getElementById("demo-start");
    const pause = document.getElementById("demo-pause");
    const skip = document.getElementById("demo-skip");
    const reset = document.getElementById("demo-reset");
    if (start) start.addEventListener("click", function () { resetDemo(); });
    if (reset) reset.addEventListener("click", function () { resetDemo(); });
    if (pause) pause.addEventListener("click", function () { demoPaused = !demoPaused; });
    if (skip) skip.addEventListener("click", function () { demoStage = demoLines.length - 1; showStage(); });
    window.setInterval(function () {
      if (!demoPaused && demoStage < demoLines.length - 1) {
        demoStage += 1;
        showStage();
      }
    }, 9000);
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
