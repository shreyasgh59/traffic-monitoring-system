document.addEventListener("DOMContentLoaded", () => {
  const menu = document.querySelector(".menu");
  const sidebar = document.querySelector(".sidebar");
  if (menu && sidebar) menu.addEventListener("click", () => sidebar.classList.toggle("open"));

  const password = document.querySelector("#id_password1");
  const bars = document.querySelectorAll(".strength span");
  if (password) password.addEventListener("input", () => {
    const value = password.value;
    const score = [value.length >= 8, /[A-Z]/.test(value), /[0-9]/.test(value), /[^A-Za-z0-9]/.test(value)].filter(Boolean).length;
    bars.forEach((bar, index) => { bar.style.background = index < score ? (score < 3 ? "#f07a5a" : "#14b8a6") : "#dbe5e3"; });
  });

  const evidenceInput = document.querySelector("#id_evidence");
  const evidencePreview = document.querySelector("#evidence-preview");
  const evidenceEmpty = document.querySelector("#evidence-empty");
  const removeEvidence = document.querySelector("#remove-evidence");
  if (evidenceInput && evidencePreview && evidenceEmpty && removeEvidence) {
    evidenceInput.addEventListener("change", () => {
      const file = evidenceInput.files[0];
      if (!file) return;
      evidencePreview.src = URL.createObjectURL(file);
      evidencePreview.hidden = false;
      evidenceEmpty.hidden = true;
      removeEvidence.hidden = false;
    });
    removeEvidence.addEventListener("click", () => {
      evidenceInput.value = "";
      evidencePreview.removeAttribute("src");
      evidencePreview.hidden = true;
      evidenceEmpty.hidden = false;
      removeEvidence.hidden = true;
    });
  }

  document.querySelectorAll("[data-density-gauge]").forEach((card) => {
    const density = Math.max(0, Math.min(100, Number(card.dataset.density) || 0));
    const value = card.querySelector(".gauge-value");
    const number = card.querySelector(".gauge-copy b");
    const status = card.querySelector(".density-status");
    const color = density >= 70 ? "#ef476f" : density >= 40 ? "#f9c74f" : "#23c58f";
    value.style.strokeDasharray = "575";
    requestAnimationFrame(() => { value.style.strokeDashoffset = String(575 - (575 * density / 100)); });
    number.textContent = `${Math.round(density)}%`;
    number.style.color = color;
    status.textContent = density >= 70 ? "Heavy" : density >= 40 ? "Medium" : "Low";
    status.style.color = color;
  });

  document.querySelectorAll("[data-congestion-chart]").forEach((chart) => {
    const draw = (points) => {
      if (!points.length) { chart.innerHTML = '<p class="muted">Congestion history will appear after the first analysis.</p>'; return; }
      const width = 620, height = 240, pad = 28;
      const coordinates = points.map((point, index) => {
        const x = pad + (index * (width - pad * 2) / Math.max(points.length - 1, 1));
        const y = height - pad - (Math.min(100, Math.max(0, point.score)) / 100 * (height - pad * 2));
        return [x.toFixed(1), y.toFixed(1)];
      });
      const line = coordinates.map((point, index) => `${index ? "L" : "M"}${point[0]} ${point[1]}`).join(" ");
      const area = `${line} L ${coordinates.at(-1)[0]} ${height - pad} L ${coordinates[0][0]} ${height - pad} Z`;
      chart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Live congestion score chart"><defs><linearGradient id="congestion-fill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#14b8a6" stop-opacity=".45"/><stop offset="1" stop-color="#14b8a6" stop-opacity=".03"/></linearGradient></defs><path class="chart-grid" d="M${pad} ${pad}H${width-pad} M${pad} ${height/2}H${width-pad} M${pad} ${height-pad}H${width-pad}"/><path d="${area}" fill="url(#congestion-fill)"/><path d="${line}" class="chart-line"/>${coordinates.map((point) => `<circle cx="${point[0]}" cy="${point[1]}" r="4"/>`).join("")}</svg><div class="chart-labels">${points.map((point) => `<span>${point.label}</span>`).join("")}</div>`;
    };
    const refresh = () => fetch(chart.dataset.historyUrl, { credentials: "same-origin" }).then((response) => response.ok ? response.json() : Promise.reject()).then((data) => draw(data.points)).catch(() => { chart.innerHTML = '<p class="muted">Live congestion data is unavailable.</p>'; });
    refresh();
    window.setInterval(refresh, 15000);
  });

  const player = document.querySelector("#monitor-player");
  const ipCamera = document.querySelector("#ip-camera-url");
  const loadIpCamera = document.querySelector("#load-ip-camera");
  const browserCamera = document.querySelector("#browser-camera");
  let browserStream = null;
  const blankPlayer = () => {
    if (browserStream) { browserStream.getTracks().forEach((track) => track.stop()); browserStream = null; }
    if (!player) return;
    player.dataset.activeSource = "";
    player.innerHTML = '<div class="source-placeholder" id="source-placeholder"><b>▣</b><h2>No Video Source Selected</h2><p>Select a source from the queue or camera controls below.</p></div>';
  };
  const setIpCamera = () => {
    const url = ipCamera?.value.trim();
    if (!url || !player) return;
    if (player.dataset.activeSource === url) { blankPlayer(); return; }
    if (browserStream) { browserStream.getTracks().forEach((track) => track.stop()); browserStream = null; }
    const image = document.createElement("img");
    image.src = url;
    image.alt = "IP webcam stream";
    player.replaceChildren(image);
    player.dataset.activeSource = url;
  };
  if (loadIpCamera) loadIpCamera.addEventListener("click", setIpCamera);
  if (ipCamera) ipCamera.addEventListener("keydown", (event) => { if (event.key === "Enter") { event.preventDefault(); setIpCamera(); } });
  if (browserCamera && navigator.mediaDevices?.enumerateDevices) {
    navigator.mediaDevices.enumerateDevices().then((devices) => devices.filter((device) => device.kind === "videoinput").forEach((device, index) => {
      const option = document.createElement("option"); option.value = device.deviceId; option.textContent = device.label || `Camera ${index + 1}`; browserCamera.append(option);
    })).catch(() => {});
    browserCamera.addEventListener("change", async () => {
      const deviceId = browserCamera.value;
      if (!deviceId || player?.dataset.activeSource === `camera:${deviceId}`) { blankPlayer(); return; }
      try {
        if (browserStream) browserStream.getTracks().forEach((track) => track.stop());
        browserStream = await navigator.mediaDevices.getUserMedia({ video: { deviceId: { exact: deviceId } }, audio: false });
        const video = document.createElement("video"); video.autoplay = true; video.muted = true; video.playsInline = true; video.srcObject = browserStream;
        player.replaceChildren(video); player.dataset.activeSource = `camera:${deviceId}`;
      } catch (_) { blankPlayer(); }
    });
  }
});
