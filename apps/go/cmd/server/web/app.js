(function () {
  "use strict";

  // -- Epoch metadata matching the Go simulator --
  var EPOCH_INFO = {
    "Planck":          { desc: "Quantum gravity dominates; spacetime foam",                  css: "planck" },
    "Inflation":       { desc: "Exponential expansion of spacetime",                         css: "inflation" },
    "Electroweak":     { desc: "Electroweak symmetry breaking; W/Z bosons acquire mass",     css: "electroweak" },
    "QuarkGluon":      { desc: "Quark-gluon plasma; free quarks and gluons",                 css: "quarkgluon" },
    "Hadron":          { desc: "Quarks confine into protons and neutrons",                   css: "hadron" },
    "Nucleosynthesis": { desc: "Light nuclei form: H, He, Li",                              css: "nucleosynthesis" },
    "Recombination":   { desc: "Electrons captured by nuclei; atoms form",                   css: "recombination" },
    "StarFormation":   { desc: "First stars ignite; heavy element forging",                  css: "starformation" },
    "SolarSystem":     { desc: "Protoplanetary disk collapses; planets form",                css: "solarsystem" },
    "EarthFormation":  { desc: "Rocky planet cools; oceans condense",                        css: "earthformation" },
    "LifeEmergence":   { desc: "First protocells arise from prebiotic chemistry",            css: "lifeemergence" },
    "DNAEvolution":    { desc: "DNA replication, mutation, and natural selection",            css: "dnaevolution" },
    "Present":         { desc: "Complex life; billions of years of evolution",               css: "present" }
  };

  var PRESENT_EPOCH = 300000;

  // Particle rendering colors
  var PARTICLE_COLORS = {
    "up":       "#ff4466", "down":     "#ff8844",
    "electron": "#4488ff", "positron": "#44ddff",
    "neutrino": "#888aaa", "photon":   "#ffff66",
    "gluon":    "#44ff66", "W":        "#ff44ff",
    "Z":        "#aa44ff", "proton":   "#ff6644",
    "neutron":  "#6688bb", "unknown":  "#555577"
  };

  // -- DOM references --
  var $ = function (id) { return document.getElementById(id); };
  var statusDot       = $("statusDot");
  var statusText      = $("statusText");
  var epochNameEl     = $("epochName");
  var epochDescEl     = $("epochDesc");
  var progressBar     = $("progressBar");
  var progressLabel   = $("progressLabel");
  var tempValue       = $("tempValue");
  var countParticles  = $("countParticles");
  var countAtoms      = $("countAtoms");
  var countMolecules  = $("countMolecules");
  var countCells      = $("countCells");
  var completeBanner  = $("completeBanner");
  var completeText    = $("completeText");
  var logEntries      = $("logEntries");
  var fieldCanvas     = $("fieldCanvas");
  var sparkCanvas     = $("sparkCanvas");
  var starsCanvas     = $("starsCanvas");

  // -- Stars background --
  function drawStars() {
    var ctx = starsCanvas.getContext("2d");
    starsCanvas.width  = window.innerWidth;
    starsCanvas.height = window.innerHeight;
    ctx.fillStyle = "#000005";
    ctx.fillRect(0, 0, starsCanvas.width, starsCanvas.height);
    for (var i = 0; i < 350; i++) {
      var x = Math.random() * starsCanvas.width;
      var y = Math.random() * starsCanvas.height;
      var r = Math.random() * 1.4 + 0.2;
      var a = Math.random() * 0.7 + 0.25;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(200,200,255," + a + ")";
      ctx.fill();
    }
  }
  drawStars();
  window.addEventListener("resize", drawStars);

  // -- Quantum field canvas --
  var fieldCtx, fieldW, fieldH;
  function resizeField() {
    var rect = fieldCanvas.parentElement.getBoundingClientRect();
    fieldW = Math.floor(rect.width);
    fieldH = Math.floor(rect.height);
    fieldCanvas.width  = fieldW;
    fieldCanvas.height = fieldH;
    fieldCtx = fieldCanvas.getContext("2d");
  }
  resizeField();
  window.addEventListener("resize", resizeField);

  var lastPositions = [];
  var lastTypes     = [];

  function drawField() {
    if (!fieldCtx) return;
    fieldCtx.fillStyle = "rgba(2, 2, 8, 0.28)";
    fieldCtx.fillRect(0, 0, fieldW, fieldH);
    if (lastPositions.length === 0) return;

    var minX = Infinity, maxX = -Infinity;
    var minY = Infinity, maxY = -Infinity;
    for (var i = 0; i < lastPositions.length; i++) {
      var p = lastPositions[i];
      if (p[0] < minX) minX = p[0];
      if (p[0] > maxX) maxX = p[0];
      if (p[1] < minY) minY = p[1];
      if (p[1] > maxY) maxY = p[1];
    }
    var rx = (maxX - minX) || 1;
    var ry = (maxY - minY) || 1;
    var pad = 0.12;
    minX -= rx * pad; maxX += rx * pad;
    minY -= ry * pad; maxY += ry * pad;
    rx = maxX - minX; ry = maxY - minY;

    for (var i = 0; i < lastPositions.length; i++) {
      var p = lastPositions[i];
      var t = lastTypes[i] || "unknown";
      var sx = ((p[0] - minX) / rx) * fieldW;
      var sy = ((p[1] - minY) / ry) * fieldH;
      var color = PARTICLE_COLORS[t] || PARTICLE_COLORS["unknown"];

      // Glow
      fieldCtx.beginPath();
      fieldCtx.arc(sx, sy, 6, 0, Math.PI * 2);
      fieldCtx.fillStyle = hexToRGBA(color, 0.12);
      fieldCtx.fill();

      // Dot
      fieldCtx.beginPath();
      fieldCtx.arc(sx, sy, 2.5, 0, Math.PI * 2);
      fieldCtx.fillStyle = color;
      fieldCtx.fill();
    }
  }

  function hexToRGBA(hex, alpha) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    return "rgba(" + r + "," + g + "," + b + "," + alpha + ")";
  }

  // Animate field at steady framerate
  (function animLoop() {
    drawField();
    requestAnimationFrame(animLoop);
  })();

  // -- Sparkline: particle count history --
  var sparkHistory = [];
  var SPARK_MAX = 200;
  var sparkCtx, sparkW, sparkH;

  function resizeSpark() {
    var rect = sparkCanvas.parentElement.getBoundingClientRect();
    sparkW = Math.floor(rect.width);
    sparkH = Math.floor(rect.height);
    sparkCanvas.width  = sparkW;
    sparkCanvas.height = sparkH;
    sparkCtx = sparkCanvas.getContext("2d");
  }
  resizeSpark();
  window.addEventListener("resize", resizeSpark);

  function pushSparkValue(val) {
    sparkHistory.push(val);
    if (sparkHistory.length > SPARK_MAX) {
      sparkHistory.shift();
    }
  }

  function drawSparkline() {
    if (!sparkCtx || sparkHistory.length < 2) return;
    sparkCtx.clearRect(0, 0, sparkW, sparkH);

    var maxVal = 1;
    for (var i = 0; i < sparkHistory.length; i++) {
      if (sparkHistory[i] > maxVal) maxVal = sparkHistory[i];
    }

    var step = sparkW / (SPARK_MAX - 1);
    var offsetX = (SPARK_MAX - sparkHistory.length) * step;

    // Fill gradient
    var grad = sparkCtx.createLinearGradient(0, 0, 0, sparkH);
    grad.addColorStop(0, "rgba(255, 102, 136, 0.25)");
    grad.addColorStop(1, "rgba(255, 102, 136, 0.02)");

    sparkCtx.beginPath();
    sparkCtx.moveTo(offsetX, sparkH);
    for (var i = 0; i < sparkHistory.length; i++) {
      var x = offsetX + i * step;
      var y = sparkH - (sparkHistory[i] / maxVal) * (sparkH - 4);
      sparkCtx.lineTo(x, y);
    }
    sparkCtx.lineTo(offsetX + (sparkHistory.length - 1) * step, sparkH);
    sparkCtx.closePath();
    sparkCtx.fillStyle = grad;
    sparkCtx.fill();

    // Line
    sparkCtx.beginPath();
    for (var i = 0; i < sparkHistory.length; i++) {
      var x = offsetX + i * step;
      var y = sparkH - (sparkHistory[i] / maxVal) * (sparkH - 4);
      if (i === 0) sparkCtx.moveTo(x, y);
      else sparkCtx.lineTo(x, y);
    }
    sparkCtx.strokeStyle = "#ff6688";
    sparkCtx.lineWidth = 1.5;
    sparkCtx.stroke();

    // Current value dot
    if (sparkHistory.length > 0) {
      var lx = offsetX + (sparkHistory.length - 1) * step;
      var ly = sparkH - (sparkHistory[sparkHistory.length - 1] / maxVal) * (sparkH - 4);
      sparkCtx.beginPath();
      sparkCtx.arc(lx, ly, 3, 0, Math.PI * 2);
      sparkCtx.fillStyle = "#ff6688";
      sparkCtx.fill();
      sparkCtx.beginPath();
      sparkCtx.arc(lx, ly, 6, 0, Math.PI * 2);
      sparkCtx.fillStyle = "rgba(255,102,136,0.2)";
      sparkCtx.fill();
    }
  }

  // -- Temperature formatting (logarithmic-aware) --
  function formatTemp(t) {
    if (t === undefined || t === null) return "--";
    if (Math.abs(t) >= 1e6) return t.toExponential(2) + " K";
    if (Math.abs(t) >= 1000) return t.toFixed(0) + " K";
    return t.toFixed(2) + " K";
  }

  // -- Progress bar --
  var currentEpochCSS = "";

  function updateProgress(tick) {
    var pct = Math.min(100, (tick / PRESENT_EPOCH) * 100);
    progressBar.style.width = pct.toFixed(1) + "%";
    progressLabel.textContent = pct.toFixed(1) + "%";
  }

  function setEpochClass(epochName) {
    var info = EPOCH_INFO[epochName];
    if (!info) return;
    var newCSS = "epoch-" + info.css;
    if (newCSS !== currentEpochCSS) {
      // Remove old epoch class
      if (currentEpochCSS) {
        progressBar.classList.remove(currentEpochCSS);
      }
      progressBar.classList.add(newCSS);
      currentEpochCSS = newCSS;
    }
  }

  // -- Counter card glow --
  function setActive(card, val) {
    if (val > 0) {
      card.classList.add("active");
    } else {
      card.classList.remove("active");
    }
  }

  // -- Event log --
  var logCount = 0;
  var MAX_LOG = 150;

  function addLog(tag, tagClass, message) {
    var el = document.createElement("div");
    el.className = "log-entry";
    el.innerHTML = '<span class="tag ' + tagClass + '">' + tag + '</span>' + escapeHTML(message);
    logEntries.insertBefore(el, logEntries.firstChild);
    logCount++;
    while (logCount > MAX_LOG && logEntries.lastChild) {
      logEntries.removeChild(logEntries.lastChild);
      logCount--;
    }
  }

  function escapeHTML(s) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(s));
    return div.innerHTML;
  }

  // -- SSE connection with auto-reconnect --
  var reconnectDelay = 1000;
  var MAX_RECONNECT_DELAY = 10000;
  var evtSource = null;

  function connect() {
    statusDot.className = "status-dot";
    statusText.textContent = "Connecting...";

    evtSource = new EventSource("/events");

    evtSource.onopen = function () {
      statusDot.className = "status-dot connected";
      statusText.textContent = "Connected - waiting for data...";
      reconnectDelay = 1000;
    };

    evtSource.onmessage = function (e) {
      var data;
      try { data = JSON.parse(e.data); } catch (err) { return; }
      handleEvent(data);
    };

    evtSource.onerror = function () {
      evtSource.close();
      evtSource = null;
      statusDot.className = "status-dot error";
      statusText.textContent = "Disconnected. Reconnecting in " + (reconnectDelay / 1000).toFixed(0) + "s...";
      addLog("CONN", "info", "Connection lost. Retrying...");
      setTimeout(function () {
        reconnectDelay = Math.min(reconnectDelay * 2, MAX_RECONNECT_DELAY);
        connect();
      }, reconnectDelay);
    };
  }

  // -- Handle incoming events --
  function handleEvent(data) {
    switch (data.type) {
      case "tick":
        statusDot.className = "status-dot running";
        statusText.textContent = "Simulating \u2014 " + data.epoch + " | Tick " + data.tick.toLocaleString();

        // Epoch info
        var info = EPOCH_INFO[data.epoch];
        epochNameEl.textContent = data.epoch;
        epochDescEl.textContent = info ? info.desc : "";
        setEpochClass(data.epoch);

        // Progress
        updateProgress(data.tick);

        // Temperature
        tempValue.textContent = formatTemp(data.temperature);

        // Counters
        countParticles.textContent = data.particles.toLocaleString();
        countAtoms.textContent     = data.atoms.toLocaleString();
        countMolecules.textContent = data.molecules.toLocaleString();
        countCells.textContent     = data.cells.toLocaleString();

        setActive(countParticles.parentElement, data.particles);
        setActive(countAtoms.parentElement, data.atoms);
        setActive(countMolecules.parentElement, data.molecules);
        setActive(countCells.parentElement, data.cells);

        // Sparkline
        pushSparkValue(data.particles);
        drawSparkline();

        // Particle positions for field canvas
        if (data.particle_pos) {
          lastPositions = data.particle_pos;
          lastTypes     = data.particle_types || [];
        }
        break;

      case "epoch_start":
        var info = EPOCH_INFO[data.epoch];
        epochNameEl.textContent = data.epoch;
        epochDescEl.textContent = info ? info.desc : "";
        setEpochClass(data.epoch);
        addLog("EPOCH", "epoch", data.epoch + " begins");
        break;

      case "complete":
        statusDot.className = "status-dot complete";
        statusText.textContent = "Simulation complete";
        completeBanner.style.display = "block";
        var elapsed = data.elapsed_ms;
        var secs = (elapsed / 1000).toFixed(2);
        completeText.textContent = "The universe evolved in " + secs + " seconds (" + elapsed + " ms).";
        addLog("DONE", "done", "Simulation finished in " + secs + "s");
        updateProgress(PRESENT_EPOCH);
        break;
    }
  }

  // Start the connection.
  connect();
})();
