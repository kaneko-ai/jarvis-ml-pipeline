/** Run List Component for JARVIS Dashboard (Phase 20). */

const runList = {
    render(containerId, runsIndex) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const tbody = container.querySelector("tbody");
        if (!tbody) return;

        tbody.innerHTML = "";

        // Convert map to sorted array (newest first)
        const runs = Object.entries(runsIndex || {})
            .map(([id, meta]) => ({ run_id: id, ...meta }))
            .sort((a, b) => b.started_at.localeCompare(a.started_at));

        if (runs.length === 0) {
            return;
        }

        runs.slice(0, 10).forEach(run => {
            const tr = document.createElement("tr");

            const badgeClass = run.status === "success" ? "success" :
                (run.status === "failed" ? "danger" : "warning");

            const finishedAt = run.finished_at ? new Date(run.finished_at).toLocaleString() : "-";

            tr.innerHTML = `
                <td>${run.run_id}</td>
                <td>${run.status}</td>
                <td>${finishedAt}</td>
                <td>
                    <a href="run.html?run_id=${run.run_id}" class="badge">View</a>
                    ${run.status === "success" ? `<a href="runs/${run.run_id}/artifacts/report.md" target="_blank" class="badge">Report</a>` : ""}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
};

window.runList = runList;
