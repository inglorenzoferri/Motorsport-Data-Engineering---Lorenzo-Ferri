/**
 * app.js — versione per sito statico (GitHub Pages)
 * --------------------------------------------------
 * Legge i JSON precalcolati dalla pipeline (pipeline/generate_data.py)
 * pubblicati in frontend/data/. Nessun backend a runtime: i dati di una
 * sessione F1 sono immutabili una volta conclusa, quindi vengono
 * precalcolati una sola volta e serviti come file statici.
 *
 * Nota di sicurezza: nessun dato dinamico è inserito con innerHTML;
 * le tabelle sono costruite con createElement/textContent.
 */

const COLORS = {
  grid: "#2b3138",
  text: "#8b939c",
  amber: "#c9a227",
  blue: "#4a90a4",
  green: "#6b9b5e",
  red: "#b3503a",
};

const DRIVER_PALETTE = [COLORS.amber, COLORS.blue, COLORS.green, COLORS.red, "#9b7dbf", "#c97d4a"];

const SESSION_LABELS = { FP1: "Libere 1", FP2: "Libere 2", FP3: "Libere 3", Q: "Qualifica", S: "Sprint", R: "Gara" };

let SESSION_INDEX = [];   // contenuto di data/index.json
let CURRENT = null;       // sessione selezionata { year, slug, event, session, drivers, sample }

function dataPath(...parts) {
  return ["data", ...parts].join("/");
}

function setStatus(message, kind) {
  const el = document.getElementById("status");
  el.textContent = message;
  el.className = "status-line" + (kind ? " " + kind : "");
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Dati non trovati (${res.status}): ${url}`);
  return res.json();
}

function plotlyBaseLayout(extra) {
  return Object.assign(
    {
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: "IBM Plex Mono, monospace", color: COLORS.text, size: 11 },
      margin: { l: 55, r: 20, t: 10, b: 45 },
      xaxis: { gridcolor: COLORS.grid, zerolinecolor: COLORS.grid },
      yaxis: { gridcolor: COLORS.grid, zerolinecolor: COLORS.grid },
      legend: { orientation: "h", y: -0.2 },
    },
    extra || {}
  );
}

/** Costruisce una <table> senza innerHTML. */
function renderTable(container, columns, rows) {
  container.textContent = "";
  const table = document.createElement("table");
  table.className = "data-table";
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col.label;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);
  table.appendChild(thead);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      const value = row[col.key];
      td.textContent = value === null || value === undefined ? "—" : String(value);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.appendChild(table);
}

/* ------------------------------------------------------------------ */
/* Selettore sessione basato su data/index.json                        */
/* ------------------------------------------------------------------ */
async function initSessionPicker() {
  try {
    SESSION_INDEX = await fetchJSON(dataPath("index.json"));
  } catch {
    setStatus("Nessun dato pubblicato: esegui la pipeline (vedi README) per generare la prima sessione.", "error");
    return;
  }

  const sel = document.getElementById("f-session-pick");
  sel.textContent = "";
  SESSION_INDEX.forEach((entry, i) => {
    const opt = document.createElement("option");
    opt.value = String(i);
    const label = SESSION_LABELS[entry.session] || entry.session;
    opt.textContent = `${entry.year} · ${entry.event} · ${label}` + (entry.sample ? " (dati di esempio)" : "");
    sel.appendChild(opt);
  });

  if (SESSION_INDEX.length > 0) {
    sel.value = "0";
    await selectSession(0);
  }
}

async function selectSession(i) {
  CURRENT = SESSION_INDEX[i];
  if (!CURRENT) return;

  const banner = document.getElementById("sample-banner");
  banner.hidden = !CURRENT.sample;

  const drvInput = document.getElementById("f-drivers");
  const available = CURRENT.drivers || [];
  drvInput.value = available.slice(0, 2).join(",");
  drvInput.placeholder = "Disponibili: " + available.join(", ");

  const exportLink = document.getElementById("btn-export");
  exportLink.href = dataPath(String(CURRENT.year), CURRENT.slug, CURRENT.session, "laps.csv");

  setStatus("Caricamento sessione…");
  try {
    await Promise.all([loadRacePace(), loadStrategy()]);
    setStatus(
      `Sessione caricata (dati generati il ${CURRENT.generated_utc ? CURRENT.generated_utc.slice(0, 10) : "—"} UTC).`,
      "ok"
    );
  } catch (err) {
    setStatus(`Errore: ${err.message}`, "error");
  }
}

function sessionBase() {
  return dataPath(String(CURRENT.year), CURRENT.slug, CURRENT.session);
}

/* ------------------------------------------------------------------ */
/* 01 — Passo gara                                                      */
/* ------------------------------------------------------------------ */
async function loadRacePace() {
  const data = await fetchJSON(sessionBase() + "/pace.json");
  const sorted = [...data].filter((d) => d.median_laptime_s != null);
  const trace = {
    type: "bar",
    x: sorted.map((d) => d.Driver),
    y: sorted.map((d) => d.median_laptime_s),
    marker: { color: COLORS.amber },
    error_y: { type: "data", array: sorted.map((d) => d.std_laptime_s || 0), color: COLORS.text },
    hovertemplate: "%{x}: %{y:.3f} s<extra></extra>",
  };
  Plotly.newPlot("chart-pace", [trace],
    plotlyBaseLayout({ yaxis: { title: "Tempo mediano sul giro (s)", gridcolor: COLORS.grid } }),
    { responsive: true, displayModeBar: false });
}

/* ------------------------------------------------------------------ */
/* 02 — Telemetria comparata (velocità + RPM)                           */
/* ------------------------------------------------------------------ */
async function loadTelemetry() {
  const requested = document.getElementById("f-drivers").value
    .split(",").map((d) => d.trim().toUpperCase()).filter(Boolean).slice(0, 6);

  const traces = [];
  for (let i = 0; i < requested.length; i++) {
    const drv = requested[i];
    let rows;
    try {
      rows = await fetchJSON(sessionBase() + `/telemetry/${drv}.json`);
    } catch {
      continue; // pilota senza telemetria in questa sessione
    }
    const color = DRIVER_PALETTE[i % DRIVER_PALETTE.length];
    traces.push({
      type: "scatter", mode: "lines", name: `${drv} · velocità`,
      x: rows.map((r) => r.Distance), y: rows.map((r) => r.Speed),
      line: { color, width: 1.8 },
    });
    if (rows[0] && rows[0].RPM !== undefined) {
      traces.push({
        type: "scatter", mode: "lines", name: `${drv} · RPM`,
        x: rows.map((r) => r.Distance), y: rows.map((r) => r.RPM),
        yaxis: "y2", line: { color, width: 1, dash: "dot" }, opacity: 0.6,
      });
    }
  }
  if (traces.length === 0) throw new Error("Nessuna telemetria disponibile per i piloti indicati.");

  Plotly.newPlot("chart-telemetry", traces,
    plotlyBaseLayout({
      xaxis: { title: "Distanza nel giro (m)", gridcolor: COLORS.grid },
      yaxis: { title: "Velocità (km/h)", gridcolor: COLORS.grid },
      yaxis2: { title: "RPM", overlaying: "y", side: "right", showgrid: false },
    }),
    { responsive: true, displayModeBar: false });
}

/* ------------------------------------------------------------------ */
/* 03 — Strategia gomme                                                 */
/* ------------------------------------------------------------------ */
async function loadStrategy() {
  const data = await fetchJSON(sessionBase() + "/strategy.json");
  renderTable(document.getElementById("table-strategy"), [
    { key: "Driver", label: "Pilota" },
    { key: "Stint", label: "Stint" },
    { key: "Compound", label: "Mescola" },
    { key: "start_lap", label: "Giro iniz." },
    { key: "end_lap", label: "Giro fin." },
    { key: "lap_count", label: "N. giri" },
  ], data);
}

/* ------------------------------------------------------------------ */
/* 04 — Dati avanzati                                                   */
/* ------------------------------------------------------------------ */
async function loadResults() {
  const data = await fetchJSON(sessionBase() + "/results.json");
  const cols = ["Position", "DriverNumber", "Abbreviation", "TeamName", "Time", "Status", "Points"]
    .filter((k) => data[0] && k in data[0])
    .map((k) => ({ key: k, label: k }));
  renderTable(document.getElementById("table-advanced"), cols, data);
}

async function loadTrackStatus() {
  const data = await fetchJSON(sessionBase() + "/track_status.json");
  const rows = data.track_status || [];
  const cols = ["Time", "Status", "Message"].filter((k) => rows[0] && k in rows[0]).map((k) => ({ key: k, label: k }));
  renderTable(document.getElementById("table-advanced"), cols, rows);
}

/* ------------------------------------------------------------------ */
/* Eventi                                                               */
/* ------------------------------------------------------------------ */
function bindHandlers() {
  document.getElementById("f-session-pick").addEventListener("change", (e) => {
    selectSession(Number(e.target.value));
  });
  document.getElementById("btn-telemetry").addEventListener("click", async () => {
    setStatus("Caricamento telemetria…");
    try { await loadTelemetry(); setStatus("Telemetria caricata.", "ok"); }
    catch (err) { setStatus(`Errore: ${err.message}`, "error"); }
  });
  document.getElementById("btn-results").addEventListener("click", async () => {
    try { await loadResults(); setStatus("Classifica caricata.", "ok"); }
    catch (err) { setStatus(`Errore: ${err.message}`, "error"); }
  });
  document.getElementById("btn-trackstatus").addEventListener("click", async () => {
    try { await loadTrackStatus(); setStatus("Dati caricati.", "ok"); }
    catch (err) { setStatus(`Errore: ${err.message}`, "error"); }
  });
}

bindHandlers();
initSessionPicker();
