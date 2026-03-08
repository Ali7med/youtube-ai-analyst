// Shared Chart.js configuration
Chart.defaults.color = '#a0a0a8';
Chart.defaults.font.family = 'Inter';

window.appCharts = {};

window.initDashboardCharts = async () => {
    try {
        const res = await fetch('/api/videos?limit=200');
        const data = await res.json();
        const videos = data.videos || [];

        if (videos.length === 0) {
            console.log("No videos found to render charts.");
            return;
        }

        // Update top-level Stats
        const avgRate = videos.reduce((sum, v) => sum + (v.rate || 0), 0) / videos.length;
        const posCount = videos.filter(v => v.sentiment === 'positive').length;

        document.getElementById('stat-total').innerText = videos.length;
        document.getElementById('stat-avg').innerText = avgRate.toFixed(1);
        document.getElementById('stat-sent').innerText = Math.round((posCount / videos.length) * 100) + '%';

        // 1. Score Distribution (Bar)
        const distribution = { '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0 };
        videos.forEach(v => {
            const r = v.rate || 0;
            if (r <= 20) distribution['0-20']++;
            else if (r <= 40) distribution['21-40']++;
            else if (r <= 60) distribution['41-60']++;
            else if (r <= 80) distribution['61-80']++;
            else distribution['81-100']++;
        });

        const ctxScore = document.getElementById('scoreChart');
        if (ctxScore) {
            if (window.appCharts.scoreChart) window.appCharts.scoreChart.destroy();
            window.appCharts.scoreChart = new Chart(ctxScore, {
                type: 'bar',
                data: {
                    labels: Object.keys(distribution),
                    datasets: [{
                        label: 'Videos',
                        data: Object.values(distribution),
                        backgroundColor: 'rgba(99, 102, 241, 0.7)',
                        borderColor: '#6366f1',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // 2. Sentiment Pie
        const sentiments = { positive: 0, neutral: 0, negative: 0 };
        videos.forEach(v => {
            const s = (v.sentiment || 'neutral').toLowerCase();
            if (sentiments[s] !== undefined) sentiments[s]++;
        });

        const ctxSentiment = document.getElementById('sentimentChart');
        if (ctxSentiment) {
            if (window.appCharts.sentimentChart) window.appCharts.sentimentChart.destroy();
            window.appCharts.sentimentChart = new Chart(ctxSentiment, {
                type: 'doughnut',
                data: {
                    labels: ['Positive', 'Neutral', 'Negative'],
                    datasets: [{
                        data: [sentiments.positive, sentiments.neutral, sentiments.negative],
                        backgroundColor: ['#10b981', '#6b6b72', '#ef4444'],
                        borderWidth: 0,
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                    cutout: '70%'
                }
            });
        }

        // 3. Rate Over Time (Line)
        const dates = {};
        videos.forEach(v => {
            if (!v.processed_at) return;
            const dateStr = v.processed_at.split(' ')[0];
            if (!dates[dateStr]) dates[dateStr] = { sum: 0, count: 0 };
            dates[dateStr].sum += (v.rate || 0);
            dates[dateStr].count++;
        });

        const sortedDates = Object.keys(dates).sort();
        const dateAverages = sortedDates.map(d => dates[d].sum / dates[d].count);

        const ctxTrend = document.getElementById('trendChart');
        if (ctxTrend && sortedDates.length > 0) {
            if (window.appCharts.trendChart) window.appCharts.trendChart.destroy();
            window.appCharts.trendChart = new Chart(ctxTrend, {
                type: 'line',
                data: {
                    labels: sortedDates,
                    datasets: [{
                        label: 'Average Rate',
                        data: dateAverages,
                        borderColor: '#ec4899',
                        backgroundColor: 'rgba(236, 72, 153, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }

        // Render Top Videos list
        const topList = document.getElementById('top-videos-list');
        if (topList) {
            const sorted = [...videos].sort((a, b) => (b.rate || 0) - (a.rate || 0)).slice(0, 5);
            topList.innerHTML = sorted.map(v => window.createVideoCard ? window.createVideoCard(v) : `<div>${v.title}</div>`).join('');
        }

    } catch (e) {
        console.error("Error drawing charts:", e);
    }
}

// Global initialization override
window.initDashboard = function () {
    console.log("Dashboard view initialized.");
    setTimeout(window.initDashboardCharts, 100);
}
