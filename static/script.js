document.addEventListener("DOMContentLoaded", () => {
    // --- UI Tabs Logic ---
    const tabSearch = document.getElementById("tab-search");
    const tabSettings = document.getElementById("tab-settings");
    const secSearch = document.getElementById("section-search");
    const secSettings = document.getElementById("section-settings");

    tabSearch.addEventListener("click", () => {
        tabSearch.classList.add("active");
        tabSettings.classList.remove("active");
        secSearch.classList.remove("hidden");
        secSettings.classList.add("hidden");
    });

    tabSettings.addEventListener("click", () => {
        tabSettings.classList.add("active");
        tabSearch.classList.remove("active");
        secSettings.classList.remove("hidden");
        secSearch.classList.add("hidden");
        loadConfig();
    });

    // --- Config Logic ---
    async function loadConfig() {
        try {
            const res = await fetch("/api/config");
            const data = await res.json();
            document.getElementById("YOUTUBE_API_KEY").value = data.YOUTUBE_API_KEY || "";
            document.getElementById("LLM_PROVIDER").value = data.LLM_PROVIDER || "gemini";
            document.getElementById("LLM_MODEL").value = data.LLM_MODEL || "gemini-2.0-flash";
            document.getElementById("LLM_API_KEY").value = data.LLM_API_KEY || "";
            document.getElementById("GOOGLE_SHEET_ID").value = data.GOOGLE_SHEET_ID || "";
        } catch (e) {
            console.error("Config load error", e);
        }
    }

    document.getElementById("config-form").addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            YOUTUBE_API_KEY: document.getElementById("YOUTUBE_API_KEY").value,
            LLM_PROVIDER: document.getElementById("LLM_PROVIDER").value,
            LLM_MODEL: document.getElementById("LLM_MODEL").value,
            LLM_API_KEY: document.getElementById("LLM_API_KEY").value,
            GOOGLE_SHEET_ID: document.getElementById("GOOGLE_SHEET_ID").value,
        };

        const res = await fetch("/api/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const msg = document.getElementById("save-msg");
            msg.style.display = "block";
            setTimeout(() => { msg.style.display = "none"; }, 3000);
        }
    });

    // --- Search Logic ---
    const searchForm = document.getElementById("search-form");
    const resultsContainer = document.getElementById("results-container");
    const loadingOverlay = document.getElementById("loading-overlay");

    // Hide loader on initial load
    loadingOverlay.classList.add("hidden");

    searchForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const query = document.getElementById("query").value;
        const max = document.getElementById("max_results").value;
        const order = document.getElementById("order").value;
        const dry_run = document.getElementById("dry_run").checked;

        if (!query) return;

        // Show Loading
        loadingOverlay.classList.remove("hidden");
        resultsContainer.innerHTML = "";
        resultsContainer.classList.add("hidden");

        try {
            const res = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query, max, order, dry_run })
            });
            const data = await res.json();

            if (!res.ok) {
                alert("Error: " + (data.error || "Unknown Error"));
            } else {
                renderResults(data.results);
            }
        } catch (error) {
            alert("Network Error, check the console.");
            console.error(error);
        } finally {
            loadingOverlay.classList.add("hidden");
        }
    });

    function renderResults(results) {
        if (!results || results.length === 0) {
            resultsContainer.innerHTML = "<p>No results found.</p>";
            resultsContainer.classList.remove("hidden");
            return;
        }

        results.forEach((v, index) => {
            const el = document.createElement("div");
            el.className = "video-card";
            el.style.animationDelay = `${index * 0.15}s`;

            // Setup Badge Class
            let badgeClass = "avg";
            if (v.rate >= 80) badgeClass = "viral";
            else if (v.rate >= 60) badgeClass = "high";
            
            // Format notes
            let notesHtml = (v.notes || "").split("\n")
                .map(n => n.trim())
                .filter(n => n && typeof n === "string")
                .map(n => `<li style="margin-left:5px;">${n.replace(/^[-•]\s*/, '')}</li>`)
                .join("");

            if (!notesHtml && typeof v.notes === 'string' && v.notes.includes("•")) {
                notesHtml = v.notes.split("•").filter(x => x.trim()).map(n => `<li>${n.trim()}</li>`).join("");
            } else if (!notesHtml) {
               notesHtml = `<li>${v.notes}</li>`;
            }

            el.innerHTML = `
                <div class="thumb-wrapper">
                    <img src="${v.thumbnail}" alt="Thumbnail">
                    <div class="rate-badge ${badgeClass}">${v.rate}</div>
                </div>
                <div class="video-info">
                    <h3><a href="${v.link}" target="_blank">${v.title}</a></h3>
                    <div class="stats">
                        <span>👁️ ${v.views.toLocaleString()}</span>
                        <span>👍 ${v.likes.toLocaleString()}</span>
                        <span>🎯 ${v.label}</span>
                        <span>🏷️ ${v.sentiment}</span>
                    </div>
                    <p class="summary"><strong>Summary:</strong> ${v.summary || "No summary available."}</p>
                    <ul class="notes-list">${notesHtml}</ul>
                </div>
            `;
            resultsContainer.appendChild(el);
        });
        
        resultsContainer.classList.remove("hidden");
    }
});
