class Router {
    constructor(routes) {
        this.routes = routes;
        this.root = document.getElementById('router-view');
        this.pageTitle = document.getElementById('current-page-title');

        window.addEventListener('popstate', () => this.handleRoute());

        // Intercept link clicks
        document.body.addEventListener('click', e => {
            const link = e.target.closest('a');
            if (link && link.hasAttribute('data-link')) {
                e.preventDefault();
                this.navigateTo(link.getAttribute('href'));
            }
        });

        this.handleRoute();
    }

    navigateTo(url) {
        window.history.pushState(null, null, url);
        this.handleRoute();
    }

    async handleRoute() {
        // Use pathname instead of hash
        const path = window.location.pathname || '/';
        const route = this.routes.find(r => r.path === path) || this.routes.find(r => r.path === '/');

        document.querySelectorAll('.nav-item').forEach(el => {
            el.classList.remove('active');
            if (el.getAttribute('href') === path) el.classList.add('active');
        });

        this.pageTitle.innerText = route ? route.title : 'Not Found';

        this.root.innerHTML = `<div class="loader-container"><div class="spinner"></div><p>Loading view...</p></div>`;
        try {
            if (!route) throw new Error('Page not found');
            const resp = await fetch(route.template);
            if (!resp.ok) throw new Error('Template not found: ' + route.template);
            const html = await resp.text();

            this.root.innerHTML = html;
            // innerHTML does NOT run <script> tags — we must re-append them as new nodes
            this._executeScripts(this.root);

            if (route.init) {
                setTimeout(route.init, 50);
            }
        } catch (e) {
            this.root.innerHTML = `<div style="padding:40px; color:var(--accent-danger)"><h2>❌ Failed to load view</h2><p>${e.message}</p></div>`;
        }
    }

    _executeScripts(container) {
        container.querySelectorAll('script').forEach(oldScript => {
            const newScript = document.createElement('script');
            Array.from(oldScript.attributes).forEach(attr => {
                newScript.setAttribute(attr.name, attr.value);
            });
            newScript.textContent = oldScript.textContent;
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
    }
}

window.initDashboard = function () {
    console.log("Dashboard view initialized.");
    setTimeout(window.initDashboardCharts, 100);
};

window.initResearch = async function () {
    console.log("Research loaded");

    // Check if we are loading from history
    const urlParams = new URLSearchParams(window.location.search);
    const searchId = urlParams.get('search_id');
    if (searchId) {
        document.getElementById('search-form').style.display = 'none';
        document.querySelector('.search-box h2').innerText = `View Search History (#${searchId})`;

        const resContainer = document.getElementById('stream-results');
        resContainer.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <h3>Saved Results</h3>
                    <div style="display:flex; gap:8px;">
                        <button onclick="exportData(${searchId}, 'csv')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-file-csv"></i> CSV</button>
                        <button onclick="exportData(${searchId}, 'markdown')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-markdown-logo"></i> MD</button>
                        <button onclick="exportData(${searchId}, 'json')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-brackets-curly"></i> JSON</button>
                    </div>
                </div>
                <div id="video-grid" class="cards-grid"></div>`;

        try {
            const resp = await fetch(`/api/videos?search_id=${searchId}`);
            const data = await resp.json();
            const videos = data.videos || [];
            const grid = document.getElementById('video-grid');
            if (videos.length === 0) {
                grid.innerHTML = '<p style="color:var(--text-secondary)">No videos found for this search.</p>';
            } else {
                grid.innerHTML = videos.map(v => window.createVideoCard ? window.createVideoCard(v) : `<div>${v.title}</div>`).join('');
            }
        } catch (e) {
            resContainer.innerHTML += `<p style="color:red">Error loading history videos: ${e.message}</p>`;
        }
        return; // skip normal form setup
    }

    const form = document.getElementById('search-form');
    if (!form) return;
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const q = document.getElementById('query').value;
        const max = document.getElementById('max').value;
        const order = document.getElementById('order').value;
        const resContainer = document.getElementById('stream-results');
        resContainer.innerHTML = `
            <h3 style="margin-bottom:12px;">Live Processing</h3>
            <div style="background:var(--bg-secondary); border-radius:var(--radius-sm); height:12px; overflow:hidden; border:1px solid var(--border-color); margin-bottom:12px;">
                <div id="live-progress-bar" style="width:0%; height:100%; background:var(--accent-primary); transition:width 0.3s ease;"></div>
            </div>
            <div id="live-log"></div>
            <div id="video-grid" class="cards-grid"></div>`;

        const logBox = document.getElementById('live-log');
        const grid = document.getElementById('video-grid');
        const progressBar = document.getElementById('live-progress-bar');

        let currentSearchId = null;

        const es = new EventSource(`/api/search/stream?query=${encodeURIComponent(q)}&max=${max}&order=${order}&dry_run=false`);

        es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const msg = document.createElement('div');
            msg.className = 'log-msg ' + data.type;

            if (data.type === 'start') {
                msg.innerText = `[START] ${data.message}`;
            }
            else if (data.type === 'search') {
                msg.innerText = `[SEARCH] ${data.message}`;
                currentSearchId = data.search_id; // assuming search_id is returned
            }
            else if (data.type === 'processing') {
                msg.innerText = `⏳ Processing ${data.index}/${data.total}: ${data.title}`;
                if (progressBar) progressBar.style.width = ((data.index / data.total) * 100) + '%';
            }
            else if (data.type === 'cache_hit') {
                msg.innerText = `💾 Cache hit: ${data.title} `;
            }
            else if (data.type === 'video_done') {
                msg.innerText = `✅ Done: Rate ${data.rate} — ${data.label} `;
                if (window.createVideoCard) {
                    grid.innerHTML += window.createVideoCard(data);
                }
            }
            else if (data.type === 'error') {
                msg.innerText = `❌ ${data.message} `;
            }
            else if (data.type === 'complete') {
                msg.innerText = `🏁 Complete! Processed ${data.processed}, Failed ${data.failed}.Time: ${data.duration_sec} s`;
                if (progressBar) {
                    progressBar.style.width = '100%';
                    progressBar.style.background = 'var(--accent-success)';
                }

                if (currentSearchId) {
                    const exportHtml = `
                        <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:20px; border-top:1px solid var(--border-color); padding-top:16px;">
                            <span style="font-size:12px; color:var(--text-secondary); margin-right:auto; align-self:center;">Export All Results:</span>
                            <button onclick="exportData(${currentSearchId}, 'csv')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-file-csv"></i> CSV</button>
                            <button onclick="exportData(${currentSearchId}, 'markdown')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-markdown-logo"></i> MD</button>
                            <button onclick="exportData(${currentSearchId}, 'json')" class="btn" style="padding:6px 12px; font-size:12px; background:var(--bg-glass); border:1px solid var(--border-color); color:var(--text-primary);"><i class="ph ph-brackets-curly"></i> JSON</button>
                        </div>
                    `;
                    resContainer.insertAdjacentHTML('beforeend', exportHtml);
                }
                es.close();
            }

            logBox.appendChild(msg);
            logBox.scrollTop = logBox.scrollHeight;
        };
        es.onerror = () => es.close();
    });
};

window.exportData = async function (searchId, type) {
    try {
        const resp = await fetch(`/api/export/${type}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ search_id: searchId })
        });

        if (!resp.ok) throw new Error("Export failed");

        const blob = await resp.blob();
        let filename = `research_${searchId}_${new Date().getTime()}.${type === 'markdown' ? 'md' : type}`;

        const disposition = resp.headers.get('Content-Disposition');
        if (disposition && disposition.includes('attachment')) {
            const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
            const matches = filenameRegex.exec(disposition);
            if (matches != null && matches[1]) {
                filename = matches[1].replace(/['"]/g, '');
            }
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (e) {
        console.error(e);
        alert("Failed to export data: " + e.message);
    }
};

const routes = [
    { path: '/', template: '/pages/dashboard.html', title: 'Dashboard Overview', init: () => window.initDashboard() },
    { path: '/research', template: '/pages/research.html', title: 'New Research', init: () => window.initResearch() },
    { path: '/history', template: '/pages/history.html', title: 'Research History' },
    { path: '/channels', template: '/pages/channels.html', title: 'Competitor Analysis' },
    { path: '/trends', template: '/pages/trends.html', title: 'Trend Radar' },
    { path: '/jobs', template: '/pages/jobs.html', title: 'Automated Jobs' },
    { path: '/studio', template: '/pages/studio.html', title: 'Content Studio' },
    { path: '/settings', template: '/pages/settings.html', title: 'Settings' }
];

document.addEventListener('DOMContentLoaded', () => {
    window.appRouter = new Router(routes);
});
