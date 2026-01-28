let mapTimer = null;

export function startMapPolling(robotId, options = {}) {
    const intervalMs = options.intervalMs || 5000;
    const imgEl = document.getElementById("map-image");
    const statusEl = document.getElementById("map-status");
    const updatedAtEl = document.getElementById("map-updated-at");
    const refreshBtn = document.getElementById("map-refresh-btn");

    if (!imgEl) {
        console.warn("[Map] map-image element not found");
        return;
    }

    const baseUrl = imgEl.dataset.mapUrl || "";
    if (!baseUrl) {
        if (statusEl) {
            statusEl.textContent = "Endpoint not set";
            statusEl.dataset.state = "error";
        }
        return;
    }

    const updateStatus = (text, isError = false) => {
        if (!statusEl) return;
        statusEl.textContent = text;
        statusEl.dataset.state = isError ? "error" : "ok";
    };

    const refresh = () => {
        if (refreshBtn) {
            refreshBtn.disabled = true;
        }
        updateStatus("Updating...");
        const url = `${baseUrl}?t=${Date.now()}`;
        imgEl.src = url;
    };

    imgEl.addEventListener("load", () => {
        updateStatus("OK");
        if (updatedAtEl) {
            const now = new Date();
            updatedAtEl.textContent = now.toLocaleTimeString();
        }
        if (refreshBtn) {
            refreshBtn.disabled = false;
        }
    });

    imgEl.addEventListener("error", () => {
        updateStatus("Failed to load", true);
        if (refreshBtn) {
            refreshBtn.disabled = false;
        }
    });

    if (refreshBtn) {
        refreshBtn.addEventListener("click", refresh);
    }

    refresh();
    mapTimer = window.setInterval(refresh, intervalMs);
}

export function stopMapPolling() {
    if (mapTimer) {
        window.clearInterval(mapTimer);
        mapTimer = null;
    }
}
