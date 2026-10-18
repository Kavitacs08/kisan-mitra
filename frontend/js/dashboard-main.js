/**
 * UI wiring for dashboard.html. Loads the pre-built dashboard_data.json
 * directly -- this is a build-time snapshot, not a live backend query (see
 * dashboard-data.js and the migration plan's privacy section for why).
 */
import { loadDistrictDashboard } from "./dashboard-data.js";

const statusEl = document.getElementById("status");
const refreshBtn = document.getElementById("refreshBtn");

async function loadDashboard() {
  statusEl.textContent = "Loading district data...";
  document.getElementById("dashboardContent").classList.add("hidden");
  try {
    const data = await loadDistrictDashboard();
    render(data);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = `Couldn't load dashboard data: ${err.message}`;
  }
}

function render(data) {
  document.getElementById("totalReports").textContent = data.total_diagnosis_reports;
  document.getElementById("plotsMonitored").textContent = data.plots_monitored;
  document.getElementById("clusterCount").textContent = data.active_outbreak_clusters.length;

  const generated = new Date(data.generated_at);
  document.getElementById("snapshotNote").textContent =
    `Snapshot generated ${generated.toLocaleDateString()} ${generated.toLocaleTimeString()} ` +
    "— refreshed by re-running the export script and redeploying, not live per-request.";

  const clusterBody = document.getElementById("clusterTableBody");
  clusterBody.innerHTML = "";
  if (data.active_outbreak_clusters.length === 0) {
    document.getElementById("noClustersMsg").classList.remove("hidden");
  } else {
    document.getElementById("noClustersMsg").classList.add("hidden");
    for (const c of data.active_outbreak_clusters) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${c.disease.replaceAll("_", " ")}</td>
        <td>${c.center_village}</td>
        <td>${c.report_count}</td>
        <td><span class="sev-pill sev-${c.severity}">${c.severity}</span></td>
      `;
      clusterBody.appendChild(tr);
    }
  }

  const diseaseBody = document.getElementById("diseaseTableBody");
  diseaseBody.innerHTML = "";
  const sortedDiseases = Object.entries(data.disease_counts).sort((a, b) => b[1] - a[1]);
  for (const [disease, count] of sortedDiseases) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${disease.replaceAll("_", " ")}</td><td>${count}</td>`;
    diseaseBody.appendChild(tr);
  }

  document.getElementById("mostRequested").textContent = data.most_requested_treatment
    ? data.most_requested_treatment.replaceAll("_", " ")
    : "No clear demand signal this week.";

  document.getElementById("dashboardContent").classList.remove("hidden");
}

refreshBtn.addEventListener("click", loadDashboard);
loadDashboard();
