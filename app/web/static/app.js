/* Frontend renders backend state. It must never assign REASSESS or invent HR/RR. */
(function () {
  const toast = document.getElementById("backend-connection");
  const ORDER = ["P01", "P02", "P03", "P04", "P05", "P06"];
  const STATUS_LABEL = {
    INITIALIZING: "INITIALIZING",
    BASELINING: "BASELINING",
    STABLE: "STABLE",
    CHANGE_DETECTED: "CHANGE DETECTED",
    REASSESS: "REASSESSMENT RECOMMENDED",
    SIGNAL_UNRELIABLE: "SIGNAL UNRELIABLE",
  };
  const STATUS_HINT = {
    INITIALIZING: "Establishing a signal.",
    BASELINING: "Establishing a personal baseline.",
    STABLE: "No sustained change from baseline.",
    CHANGE_DETECTED: "Verifying persistence…",
    REASSESS: "Sustained physiological change from baseline.",
    SIGNAL_UNRELIABLE: "No inference made",
  };
  const ABSTAIN_REASON = {
    motion_artifact: "Excessive movement",
    no_face: "No face",
    poor_illumination: "Poor illumination",
    insufficient_valid_frames: "Insufficient signal",
    no_spectral_peak: "No pulse peak",
    roi_disagreement: "ROI disagreement",
    low_confidence: "Low confidence",
    recovery_warmup: "Recovering signal",
  };
  const SOURCE = {
    P01: "Live camera",
    P04: "Recorded scenario",
  };

  const path = window.location.pathname;
  let selectedId = path === "/live" ? "P01" : "P04";
  let detailOpen = false;
  let evm = false;
  let lastAlert = null;
  let connected = false;
  let demoPaused = false;
  let seenAt = {};
  let latestById = {};
  let lastReliable = {};
  let lastThresholds = {};
  let previewIndex = -1;
  let fixtureCache = null;
  const PREVIEW_STEPS = [
    { key: "stable", label: "STABLE" },
    { key: "unreliable", label: "SIGNAL UNRELIABLE" },
    { key: "change_detected", label: "CHANGE DETECTED" },
    { key: "reassess", label: "REASSESS" },
  ];

  function show(message) {
    if (!toast) return;
    toast.hidden = false;
    toast.textContent = message;
  }

  function safe(obj, key, fallback) {
    if (!obj || obj[key] === undefined || obj[key] === null) return fallback;
    return obj[key];
  }

  function displayName(id) {
    return id || "Patient";
  }

  function statusText(code) {
    return STATUS_LABEL[code] || code || "INITIALIZING";
  }

  function sourceLabel(id) {
    return SOURCE[id] || "Demo context";
  }

  function waitLabel(minutes) {
    const n = Number(minutes);
    if (!Number.isFinite(n)) return "Wait —";
    if (n >= 60) {
      const hours = Math.floor(n / 60);
      const mins = Math.round(n % 60);
      return "Wait " + hours + "h" + (mins ? " " + mins + "m" : "");
    }
    return "Wait " + Math.round(n) + "m";
  }

  function ago(ts) {
    if (!ts) return null;
    const sec = Math.max(0, Math.round((Date.now() - ts) / 1000));
    if (sec < 2) return "Updated 2s ago";
    return "Updated " + sec + "s ago";
  }

  function since(ts) {
    if (!ts) return null;
    const sec = Math.max(0, Math.round((Date.now() - ts) / 1000));
    return sec + "s ago";
  }

  function pct(value) {
    if (value === null || value === undefined) return null;
    const signed = value >= 0 ? "+" : "";
    return signed + Math.round(value * 100) + "%";
  }

  function isUnreliable(patient, code) {
    return !!(patient && (code === "SIGNAL_UNRELIABLE" || patient.abstaining));
  }

  function isLiveVitals(patient, code) {
    return !!(
      connected &&
      patient &&
      !patient.simulated &&
      !isUnreliable(patient, code) &&
      patient.heart_rate != null
    );
  }

  function rememberReliable(patient, code) {
    if (!patient || patient.simulated || isUnreliable(patient, code)) return;
    if (patient.heart_rate == null) return;
    lastReliable[patient.patient_id] = {
      hr: patient.heart_rate,
      at: Date.now(),
    };
  }

  function confPct(patient, code) {
    if (!isLiveVitals(patient, code) || patient.heart_rate_confidence == null) return null;
    return Math.round(patient.heart_rate_confidence * 100) + "%";
  }

  function hrLive(patient, code) {
    if (!isLiveVitals(patient, code)) return null;
    return Math.round(patient.heart_rate) + " bpm";
  }

  function rrLive(patient, code) {
    if (!patient || patient.simulated || isUnreliable(patient, code)) return null;
    if (patient.respiratory_rate == null) return null;
    return String(patient.respiratory_rate) + "/min";
  }

  function motionWord(score) {
    if (score == null) return null;
    if (score >= 0.45) return "High";
    if (score >= 0.2) return "Moderate";
    return "Low";
  }

  function confWord(score) {
    if (score == null) return null;
    if (score >= 0.8) return "High";
    if (score >= 0.55) return "Moderate";
    return "Low";
  }

  function persistLine(patient, code) {
    if (!patient || patient.persistence_seconds == null) return null;
    const elapsed = Math.round(patient.persistence_seconds);
    const target =
      code === "CHANGE_DETECTED" ? lastThresholds.change_persistence_seconds : null;
    if (target && elapsed < Math.round(target)) {
      return elapsed + " of " + Math.round(target) + " sec";
    }
    return elapsed + " sec";
  }

  function setHealth(ok) {
    const label = document.getElementById("health-label");
    const wrap = document.getElementById("system-health");
    if (label) label.textContent = ok ? "READY" : "RECONNECTING";
    if (!wrap) return;
    const mark = wrap.querySelector(".state-mark");
    if (mark) mark.className = "state-mark " + (ok ? "STABLE" : "CHANGE_DETECTED");
  }

  function badge(code) {
    return '<span class="badge ' + code + '">' + statusText(code) + "</span>";
  }

  function openDetail(patient) {
    if (!patient) return;
    selectedId = patient.patient_id;
    detailOpen = true;
    renderDetail(patient);
    updateVideo();
    const modal = document.getElementById("patient-modal");
    if (!modal) return;
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    window.requestAnimationFrame(function () {
      modal.classList.add("is-open");
      const closeBtn = document.getElementById("modal-close");
      if (closeBtn) closeBtn.focus();
    });
  }

  function closeDetail() {
    detailOpen = false;
    const modal = document.getElementById("patient-modal");
    const img = document.getElementById("patient-video");
    if (img) img.removeAttribute("src");
    document.body.classList.remove("modal-open");
    if (!modal) return;
    modal.classList.remove("is-open");
    window.setTimeout(function () {
      if (!detailOpen) {
        modal.hidden = true;
        modal.setAttribute("aria-hidden", "true");
      }
    }, 220);
  }

  function cardHtml(id, patient, code) {
    const source = sourceLabel(id);
    const wait = waitLabel(patient.wait_minutes);
    const sim = patient.simulated ? " · sim" : "";
    const unreliable = isUnreliable(patient, code);
    let body;

    if (patient.simulated) {
      body =
        "<p class=\"vital-v\">No live measurement</p>" +
        "<p class=\"vital-sub\">Waiting-room context only</p>";
    } else if (unreliable) {
      const reason = ABSTAIN_REASON[patient.abstention_reason] || patient.abstention_reason;
      const prior = lastReliable[id];
      body =
        "<div class=\"vital-v\">—</div>" +
        "<p class=\"vital-k\">HR · RR —</p>" +
        "<p class=\"vital-sub\">Signal unreliable — no inference made</p>" +
        (reason ? "<p class=\"vital-sub\">" + reason + "</p>" : "") +
        (prior
          ? "<p class=\"vital-sub\">Last reliable HR " + Math.round(prior.hr) + " bpm · " + since(prior.at) + "</p>"
          : "<p class=\"vital-sub\">Measurement unavailable</p>");
    } else {
      const hr = hrLive(patient, code) || "—";
      const delta = pct(patient.heart_rate_delta_pct);
      const rr = rrLive(patient, code) || "RR unavailable";
      body =
        "<div class=\"vital-v\">" + hr + "</div>" +
        "<p class=\"vital-k\">HR" + (delta ? " · " + delta + " from baseline" : "") + "</p>" +
        "<p class=\"vital-sub\">" + rr + "</p>";
    }

    const conf = confPct(patient, code);
    const updated = patient.simulated ? "Context only" : ago(seenAt[id]) || "Updated —";
    const persist = persistLine(patient, code);
    const extra =
      code === "CHANGE_DETECTED"
        ? "<p class=\"vital-sub\">Verifying persistence…" + (persist ? " " + persist : "") + "</p>"
        : "";

    return (
      "<div class=\"card-top\"><span class=\"card-id\">" + displayName(id) + "</span>" + badge(code) + "</div>" +
      "<p class=\"source\">" + source + " · " + wait + sim + "</p>" +
      body + extra +
      "<p class=\"meta\"><span>" + (conf ? "Conf " + conf : "Conf —") + "</span><span>" + updated + "</span></p>" +
      "<p class=\"more\">View details →</p>"
    );
  }

  function renderBoard(snapshot) {
    const board = document.getElementById("patient-board");
    if (!board) return;
    const byId = {};
    (snapshot.patients || []).forEach(function (p) { byId[p.patient_id] = p; });
    latestById = byId;
    lastThresholds = snapshot.thresholds || lastThresholds;

    ORDER.forEach(function (id) {
      const patient = byId[id];
      if (!patient) return;
      const code = safe(patient, "status", "INITIALIZING");
      rememberReliable(patient, code);
      let card = board.querySelector('[data-patient-id="' + id + '"]');
      if (!card) {
        card = document.createElement("button");
        card.type = "button";
        card.dataset.patientId = id;
        card.addEventListener("click", function () {
          if (latestById[id]) openDetail(latestById[id]);
        });
        board.appendChild(card);
      }
      const sig = [code, patient.heart_rate, patient.abstaining, patient.persistence_seconds, patient.heart_rate_delta_pct].join("|");
      if (card.dataset.sig !== sig) {
        seenAt[id] = Date.now();
        card.dataset.sig = sig;
      } else if (!seenAt[id]) {
        seenAt[id] = Date.now();
      }
      card.className = "card " + code;
      card.setAttribute("aria-label", displayName(id) + ", " + statusText(code) + ", " + sourceLabel(id) + ". View details");
      card.innerHTML = cardHtml(id, patient, code);
    });

    const patients = snapshot.patients || [];
    const active = patients.filter(function (p) { return p.processed; }).length;
    const demo = patients.filter(function (p) { return p.simulated; }).length;
    const watching = patients.filter(function (p) { return p.status === "CHANGE_DETECTED"; }).length;
    const reassess = patients.filter(function (p) { return p.status === "REASSESS"; }).length;
    const setText = function (id, value) {
      const el = document.getElementById(id);
      if (el) el.textContent = String(value);
    };
    setText("count-active", active);
    setText("count-demo", demo);
    setText("count-watching", watching);
    setText("count-reassess", reassess);
    const counts = document.getElementById("room-counts");
    if (counts) counts.textContent = active + " active · " + watching + " watching · " + reassess + " reassess";
    setHealth(connected);
  }

  function queueButton(patient, extra) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "queue-item " + patient.status;
    const delta = pct(patient.heart_rate_delta_pct);
    const persist = persistLine(patient, patient.status);
    btn.innerHTML =
      "<strong>" + displayName(patient.patient_id) + (delta ? " · HR " + delta : "") + "</strong>" +
      "<span>" + extra + (persist ? " · " + persist : "") + "</span>";
    btn.addEventListener("click", function () { openDetail(patient); });
    return btn;
  }

  function renderQueue(snapshot) {
    const watchingBox = document.getElementById("watching-list");
    const reassessBox = document.getElementById("reassess-list");
    const patients = snapshot.patients || [];
    const watching = patients.filter(function (p) { return p.status === "CHANGE_DETECTED"; });
    const reassess = patients.filter(function (p) { return p.status === "REASSESS"; });

    if (watchingBox) {
      if (!watching.length) {
        watchingBox.innerHTML = "<p class=\"queue-empty\">No patients currently being verified.</p>";
      } else {
        watchingBox.innerHTML = "";
        watching.forEach(function (patient) {
          watchingBox.appendChild(queueButton(patient, "Verifying persistence…"));
        });
      }
    }
    if (reassessBox) {
      if (!reassess.length) {
        reassessBox.innerHTML = "<p class=\"queue-empty\">No patients currently require reassessment.</p>";
      } else {
        reassessBox.innerHTML = "";
        reassess.forEach(function (patient) {
          reassessBox.appendChild(queueButton(patient, "Reassessment recommended"));
        });
      }
    }
  }

  function addMetric(html, label, value) {
    if (value == null || value === "") return html;
    return html + "<dt>" + label + "</dt><dd>" + value + "</dd>";
  }

  function renderDetail(patient) {
    if (!patient || !detailOpen) return;
    const code = safe(patient, "status", "INITIALIZING");
    const title = document.getElementById("detail-title");
    const lead = document.getElementById("decision-lead");
    const sub = document.getElementById("decision-sub");
    const compare = document.getElementById("compare-block");
    const metrics = document.getElementById("detail-metrics");
    const why = document.getElementById("why-flagged");
    const proof = document.getElementById("tech-proof");
    const reasonLead = document.getElementById("reason-lead");
    const reasonBox = document.getElementById("reason-metrics");
    const reasonCol = document.querySelector(".detail-col.reason");
    const unreliable = isUnreliable(patient, code);

    if (reasonCol) reasonCol.className = "detail-col reason " + code;
    if (title) title.textContent = displayName(patient.patient_id) + " · " + sourceLabel(patient.patient_id);
    if (lead) {
      lead.textContent = statusText(code);
      lead.className = "decision-lead " + code;
    }
    if (sub) {
      const conf = confWord(patient.heart_rate_confidence);
      sub.textContent = STATUS_HINT[code] + (code === "REASSESS" && conf ? " Confidence: " + conf : "");
    }

    if (compare) {
      if (patient.simulated) {
        compare.innerHTML = "<div><dt>Source</dt><dd>Demo context</dd><p class=\"vital-sub\">Not a live physiological feed.</p></div>";
      } else if (unreliable) {
        const prior = lastReliable[patient.patient_id];
        compare.innerHTML =
          "<div><dt>Current</dt><dd>Unavailable</dd><p class=\"vital-sub\">Signal unreliable — no inference made</p></div>" +
          "<div><dt>Last reliable HR</dt><dd>" +
          (prior ? Math.round(prior.hr) + " bpm" : "—") +
          "</dd><p class=\"vital-sub\">" + (prior ? since(prior.at) : "No prior reliable measurement") + "</p></div>";
      } else {
        const baseHr = patient.baseline_heart_rate == null ? "—" : Math.round(patient.baseline_heart_rate) + " bpm";
        const curHr = hrLive(patient, code) || "—";
        const baseRr = patient.baseline_respiratory_rate == null ? "—" : Math.round(patient.baseline_respiratory_rate) + "/min";
        const curRr = rrLive(patient, code) || "Unavailable";
        const delta = pct(patient.heart_rate_delta_pct);
        compare.innerHTML =
          "<div><dt>Baseline</dt><dd>HR " + baseHr + "</dd><p class=\"vital-sub\">RR " + baseRr + "</p></div>" +
          "<div><dt>Current</dt><dd>HR " + curHr + "</dd><p class=\"vital-sub\">RR " + curRr + (delta ? " · " + delta : "") + "</p></div>";
      }
    }

    if (metrics) {
      let html = "";
      html = addMetric(html, "Confidence", confPct(patient, code));
      if (patient.persistence_seconds) html = addMetric(html, "Persistence", persistLine(patient, code));
      if (!patient.simulated && code !== "INITIALIZING") {
        html = addMetric(html, "Motion", motionWord(patient.motion_score));
        html = addMetric(html, "ROI agreement", confWord(patient.roi_agreement));
      }
      metrics.innerHTML = html;
    }

    if (reasonLead) reasonLead.textContent = STATUS_HINT[code] || "";
    if (reasonBox) {
      let html = "";
      html = addMetric(html, "Heart rate change", pct(patient.heart_rate_delta_pct));
      html = addMetric(html, "Persistence", persistLine(patient, code));
      html = addMetric(html, "Confidence", confWord(patient.heart_rate_confidence));
      if (!patient.simulated) {
        html = addMetric(html, "Motion", motionWord(patient.motion_score));
        html = addMetric(html, "ROI agreement", confWord(patient.roi_agreement));
      }
      reasonBox.innerHTML = html;
    }

    if (why) {
      why.innerHTML = "";
      const lines = [];
      if (patient.reasons && patient.reasons.length) {
        patient.reasons.forEach(function (reason) { lines.push(reason); });
      }
      const joined = lines.join(" ").toLowerCase();
      if ((code === "CHANGE_DETECTED" || code === "REASSESS") && patient.heart_rate_delta_pct != null && joined.indexOf("from baseline") === -1) {
        lines.push("Heart-rate estimate changed " + pct(patient.heart_rate_delta_pct) + " from this patient's established baseline.");
      }
      if ((code === "CHANGE_DETECTED" || code === "REASSESS") && patient.persistence_seconds && joined.indexOf("persist") === -1) {
        lines.push("Change persisted for " + Math.round(patient.persistence_seconds) + " seconds.");
      }
      if (unreliable && lines.indexOf("Signal unreliable — no inference made.") === -1) {
        lines.unshift("Signal unreliable — no inference made.");
      }
      if (!lines.length) lines.push(STATUS_HINT[code] || "—");
      lines.forEach(function (reason) {
        const li = document.createElement("li");
        li.textContent = reason;
        why.appendChild(li);
      });
    }

    if (proof) {
      let html = "";
      html = addMetric(html, "Backend state", code);
      html = addMetric(html, "Source", sourceLabel(patient.patient_id));
      if (!patient.simulated) {
        html = addMetric(html, "ROI agreement", patient.roi_agreement == null ? null : patient.roi_agreement.toFixed(2));
        html = addMetric(html, "Signal quality", patient.signal_quality == null ? null : patient.signal_quality.toFixed(2));
        html = addMetric(html, "Motion score", patient.motion_score == null ? null : patient.motion_score.toFixed(2));
        html = addMetric(html, "Confidence", confPct(patient, code));
        html = addMetric(html, "Baseline HR", patient.baseline_heart_rate == null ? null : Math.round(patient.baseline_heart_rate) + " bpm");
        html = addMetric(html, "Current HR", hrLive(patient, code));
        html = addMetric(html, "Change", pct(patient.heart_rate_delta_pct));
        html = addMetric(html, "Persistence", persistLine(patient, code));
        html = addMetric(html, "Abstention reason", ABSTAIN_REASON[patient.abstention_reason] || patient.abstention_reason);
      } else {
        html = addMetric(html, "Note", "Simulated waiting-room tile. Not live physiology.");
      }
      proof.innerHTML = html;
    }
  }

  function updateVideo() {
    const img = document.getElementById("patient-video");
    if (!img || !detailOpen) return;
    img.src = "/stream/" + selectedId + (evm ? "?evm=true" : "") + "&t=" + Date.now();
    const note = document.getElementById("evm-note");
    if (note) note.hidden = !evm;
    const raw = document.getElementById("btn-raw");
    const evmBtn = document.getElementById("btn-evm");
    if (raw) raw.className = evm ? "button" : "button primary";
    if (evmBtn) evmBtn.className = evm ? "button primary" : "button";
  }

  function renderDoctorAlert(snapshot) {
    const notice = document.getElementById("reassess-alert");
    const body = document.getElementById("reassess-body");
    const flagged = (snapshot.patients || []).find(function (p) { return p.status === "REASSESS"; });
    if (notice) {
      if (flagged) {
        notice.hidden = false;
        const delta = pct(flagged.heart_rate_delta_pct);
        const persist = flagged.persistence_seconds == null ? null : Math.round(flagged.persistence_seconds) + " sec";
        const conf = confPct(flagged, flagged.status);
        const bits = [];
        if (delta) bits.push("HR " + delta);
        if (persist) bits.push(persist);
        if (conf) bits.push("Confidence " + conf);
        if (body) {
          body.textContent =
            displayName(flagged.patient_id) + " has shown a sustained physiological change from their baseline." +
            (bits.length ? " " + bits.join(" · ") : "");
        }
        lastAlert = flagged.patient_id;
      } else {
        notice.hidden = true;
        lastAlert = null;
      }
    }
    const eventBox = document.getElementById("signal-event");
    if (eventBox && snapshot.event) {
      eventBox.hidden = false;
      eventBox.textContent = snapshot.event;
    }
    const cam = document.getElementById("camera-error");
    if (cam && snapshot.camera_error) {
      cam.hidden = false;
      cam.textContent = "Camera stopped. Guided Demo remains available.";
    }
  }

  function syncDemoControls(snapshot) {
    demoPaused = !!snapshot.demo_paused;
    const pauseBtn = document.getElementById("demo-pause");
    if (pauseBtn) pauseBtn.textContent = demoPaused ? "RESUME" : "PAUSE";
  }

  function applySnapshot(snapshot) {
    if (!snapshot || snapshot.type !== "snapshot") return;
    const byId = {};
    (snapshot.patients || []).forEach(function (p) { byId[p.patient_id] = p; });
    renderBoard(snapshot);
    renderQueue(snapshot);
    renderDetail(byId[selectedId] || (snapshot.patients || [])[0]);
    renderDoctorAlert(snapshot);
    syncDemoControls(snapshot);
  }

  function connect() {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(proto + "://" + window.location.host + "/ws/telemetry");
    socket.addEventListener("open", function () {
      connected = true;
      setHealth(true);
      if (toast) toast.hidden = true;
    });
    socket.addEventListener("message", function (event) {
      if (previewIndex >= 0) return;
      let data;
      try { data = JSON.parse(event.data); } catch (err) { return; }
      applySnapshot(data);
    });
    socket.addEventListener("close", function () {
      connected = false;
      setHealth(false);
      show("Backend disconnected. Reconnecting… Measurements are not live.");
      window.setTimeout(connect, 1500);
    });
  }

  function postStart(mode) {
    fetch("/api/session/start?mode=" + mode, { method: "POST" })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        if (!data.ok && data.error) show(data.error);
      })
      .catch(function () { show("Server not running."); });
  }

  const raw = document.getElementById("btn-raw");
  const evmBtn = document.getElementById("btn-evm");
  if (raw) raw.addEventListener("click", function () { evm = false; updateVideo(); });
  if (evmBtn) evmBtn.addEventListener("click", function () { evm = true; updateVideo(); });

  const viewBtn = document.getElementById("view-patient");
  if (viewBtn) {
    viewBtn.addEventListener("click", function () {
      if (!lastAlert || !latestById[lastAlert]) return;
      openDetail(latestById[lastAlert]);
    });
  }

  const closeBtn = document.getElementById("modal-close");
  const backdrop = document.getElementById("modal-backdrop");
  if (closeBtn) closeBtn.addEventListener("click", closeDetail);
  if (backdrop) backdrop.addEventListener("click", closeDetail);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && detailOpen) closeDetail();
  });

  const pauseBtn = document.getElementById("demo-pause");
  if (pauseBtn) {
    pauseBtn.addEventListener("click", function () {
      const next = !demoPaused;
      fetch("/api/session/pause?paused=" + next, { method: "POST" })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
          demoPaused = !!data.paused;
          pauseBtn.textContent = demoPaused ? "RESUME" : "PAUSE";
        })
        .catch(function () { show("Could not pause demo."); });
    });
  }

  const resetBtn = document.getElementById("demo-reset");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      fetch("/api/session/reset", { method: "POST" })
        .then(function (resp) { return resp.json(); })
        .then(function (data) {
          demoPaused = false;
          if (pauseBtn) pauseBtn.textContent = "PAUSE";
          if (!data.ok && data.error) show(data.error);
        })
        .catch(function () { show("Could not restart demo."); });
    });
  }

  const modeBtn = document.getElementById("op-mode");
  const realVsSim = document.getElementById("real-vs-sim");
  if (modeBtn && realVsSim) {
    modeBtn.addEventListener("click", function () {
      realVsSim.open = !realVsSim.open;
      modeBtn.setAttribute("aria-expanded", realVsSim.open ? "true" : "false");
      if (realVsSim.open) realVsSim.scrollIntoView({ block: "nearest" });
    });
  }

  if (path === "/" || path === "/dashboard" || path === "/demo") postStart("demo");
  if (path === "/live") postStart("live");

  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try { localStorage.setItem("triage-theme", theme); } catch (err) {}
    const themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.textContent = theme === "dark" ? "Light" : "Dark";
      themeBtn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    }
  }

  applyTheme(currentTheme());
  const themeBtn = document.getElementById("theme-toggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      applyTheme(currentTheme() === "dark" ? "light" : "dark");
    });
  }

  function previewSnapshot(sampleKey) {
    if (!fixtureCache) return;
    const snap = JSON.parse(JSON.stringify(fixtureCache.snapshot));
    const sample = fixtureCache.samples[sampleKey];
    if (!sample) return;
    snap.patients = (snap.patients || []).map(function (patient) {
      if (patient.patient_id !== "P04") return patient;
      const next = Object.assign({}, sample);
      next.patient_id = "P04";
      next.wait_minutes = 33;
      next.simulated = false;
      next.processed = true;
      return next;
    });
    snap.note = "UI test preview from /api/product-fixtures. Not live Core state.";
    applySnapshot(snap);
  }

  function setPreviewBanner(on, label) {
    const banner = document.getElementById("ui-test-banner");
    const copy = document.getElementById("ui-test-copy");
    const testBtn = document.getElementById("ui-test");
    if (banner) banner.hidden = !on;
    if (copy && on) {
      copy.textContent = "UI test preview · P04 " + label + " · not live Core state. Values come from /api/product-fixtures.";
    }
    if (testBtn) testBtn.textContent = on ? "Next state" : "Test UI";
  }

  function showPreview(index) {
    previewIndex = index;
    const step = PREVIEW_STEPS[previewIndex];
    previewSnapshot(step.key);
    setPreviewBanner(true, step.label);
  }

  function exitPreview() {
    previewIndex = -1;
    setPreviewBanner(false);
    fetch("/api/patients")
      .then(function (resp) { return resp.json(); })
      .then(applySnapshot)
      .catch(function () {});
  }

  function loadFixtures() {
    if (fixtureCache) return Promise.resolve(fixtureCache);
    return fetch("/api/product-fixtures")
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        fixtureCache = data;
        return data;
      });
  }

  function startOrAdvancePreview() {
    loadFixtures()
      .then(function () {
        const next = previewIndex < 0 ? 0 : previewIndex + 1;
        if (next >= PREVIEW_STEPS.length) {
          exitPreview();
          return;
        }
        showPreview(next);
      })
      .catch(function () { show("Could not load UI test fixtures."); });
  }

  const testBtn = document.getElementById("ui-test");
  const testNext = document.getElementById("ui-test-next");
  const testExit = document.getElementById("ui-test-exit");
  if (testBtn) testBtn.addEventListener("click", startOrAdvancePreview);
  if (testNext) testNext.addEventListener("click", startOrAdvancePreview);
  if (testExit) testExit.addEventListener("click", exitPreview);

  if (path !== "/health") connect();
})();
