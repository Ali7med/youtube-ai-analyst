const createVideoCard = (video) => {
    const rateColor = video.rate >= 80 ? 'var(--accent-success)' : video.rate >= 50 ? 'var(--accent-primary)' : 'var(--accent-danger)';
    const sentimentIcon = video.sentiment === 'positive' ? 'ph-smiley' : video.sentiment === 'negative' ? 'ph-smiley-sad' : 'ph-smiley-meh';
    const sentimentColor = video.sentiment === 'positive' ? 'var(--accent-success)' : video.sentiment === 'negative' ? 'var(--accent-danger)' : 'var(--text-secondary)';

    // Formatting numbers
    const formatNum = (num) => num ? new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num) : '0';

    // Format duration from ISO 8601 (PT9M2S) to human readable (09:02)
    const formatDuration = (pt) => {
        if (!pt || !pt.startsWith('PT')) return pt || '0:00';
        const m = pt.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
        if (!m) return pt;
        const h = parseInt(m[1] || 0), min = parseInt(m[2] || 0), s = parseInt(m[3] || 0);
        return h > 0 ? `${String(h).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(s).padStart(2, '0')}` : `${String(min).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    };

    // Language flag emoji map
    const langFlag = (code) => {
        const flags = { 'ar': '🇸🇦', 'en': '🇬🇧', 'fr': '🇫🇷', 'de': '🇩🇪', 'es': '🇪🇸', 'pt': '🇧🇷', 'ru': '🇷🇺', 'zh': '🇨🇳', 'ja': '🇯🇵', 'ko': '🇰🇷', 'tr': '🇹🇷', 'it': '🇮🇹' };
        return flags[code] || '🌐';
    };

    const videoUrl = video.link || `https://www.youtube.com/watch?v=${video.video_id}`;
    const lang = video.response_language && video.response_language !== 'unknown' ? video.response_language : null;

    return `
    <div class="card" style="display:flex; flex-direction:column; gap:16px; padding:20px;">
        
        <!-- Header: Thumbnail + Title + Stats -->
        <div style="display:flex; gap:16px; align-items:flex-start;">
            <a href="${videoUrl}" target="_blank" style="position:relative; width:160px; height:90px; border-radius:8px; overflow:hidden; flex-shrink:0; display:block;">
                <img src="${video.thumbnail || ''}" alt="Thumbnail" style="width:100%; height:100%; object-fit:cover; background:#1a1a2e; transition:0.3s; transform-origin:center;" onmouseover="this.style.transform='scale(1.05)'" onmouseleave="this.style.transform='scale(1)'">
                <div style="position:absolute; bottom:4px; right:4px; background:rgba(0,0,0,0.8); padding:2px 6px; border-radius:4px; font-size:11px; font-weight:600; color:#fff;">
                    ${formatDuration(video.duration)}
                </div>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); background:rgba(239,68,68,0.9); color:white; border-radius:50%; width:32px; height:32px; display:flex; align-items:center; justify-content:center; opacity:0; transition:0.2s;" onmouseover="this.style.opacity='1'" onmouseleave="this.style.opacity='0'">
                    <i class="ph-fill ph-play" style="font-size:16px;"></i>
                </div>
            </a>
            
            <div style="flex:1;">
                <a href="${videoUrl}" target="_blank" style="text-decoration:none;">
                    <h3 style="font-size:16px; color:var(--text-primary); margin-bottom:8px; line-height:1.4; transition:color 0.2s;" onmouseover="this.style.color='var(--accent-primary)'" onmouseleave="this.style.color='var(--text-primary)'">${video.title || 'Untitled Video'}</h3>
                </a>
                
                <div style="display:flex; flex-wrap:wrap; gap:12px; font-size:12px; color:var(--text-secondary);">
                    <div style="display:flex; align-items:center; gap:4px;"><i class="ph ph-eye"></i> ${formatNum(video.views)}</div>
                    <div style="display:flex; align-items:center; gap:4px;"><i class="ph ph-thumbs-up"></i> ${formatNum(video.likes)}</div>
                    <div style="display:flex; align-items:center; gap:4px;"><i class="ph ph-chat-circle"></i> ${formatNum(video.comments)}</div>
                </div>
                
                <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:10px;">
                    <span style="background:rgba(255,255,255,0.05); border:1px solid var(--border-color); padding:4px 8px; border-radius:4px; font-size:11px; color:var(--text-muted);">${video.label || 'Unlabeled'}</span>
                    <span style="background:rgba(255,255,255,0.05); border:1px solid var(--border-color); padding:4px 8px; border-radius:4px; font-size:11px; color:${sentimentColor}; display:flex; align-items:center; gap:4px;">
                        <i class="ph ${sentimentIcon}"></i> ${video.sentiment || 'neutral'}
                    </span>
                    ${lang ? `<span title="Content Language" style="background:rgba(99,102,241,0.08); border:1px solid var(--border-color); padding:4px 8px; border-radius:4px; font-size:11px; color:var(--text-secondary); display:flex; align-items:center; gap:4px;">${langFlag(lang)} ${lang.toUpperCase()}</span>` : ''}
                    ${video.topics ? video.topics.split(',').slice(0, 2).map(t => `<span style="background:rgba(99,102,241,0.1); color:var(--accent-primary); padding:4px 8px; border-radius:4px; font-size:11px;">#${t.trim()}</span>`).join('') : ''}
                </div>
            </div>

            <!-- Score Badge -->
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:60px; height:60px; border-radius:50%; border:3px solid ${rateColor}; flex-shrink:0;">
                <span style="font-size:18px; font-weight:800; color:${rateColor}; margin-top:-2px;">${Math.round(video.rate || 0)}</span>
                <span style="font-size:9px; color:var(--text-muted); margin-top:-4px;">SCORE</span>
            </div>
        </div>
        
        <hr style="border:0; height:1px; background:var(--border-color); margin:4px 0;">
        
        <!-- Detailed Info: AI Summary & Notes -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; font-size:13px; color:var(--text-secondary);">
            <div>
                <strong style="color:var(--text-primary); display:block; margin-bottom:6px;"><i class="ph ph-text-align-left" style="margin-right:4px;"></i>AI Summary</strong>
                <p style="line-height:1.6;">${video.summary || 'No summary available.'}</p>
            </div>
            <div>
                <strong style="color:var(--text-primary); display:block; margin-bottom:6px;"><i class="ph ph-note-pencil" style="margin-right:4px;"></i>Notes & Strategy</strong>
                <p style="line-height:1.6;">${video.notes || 'No notes available.'}</p>
            </div>
        </div>

        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px; font-size:12px; background:rgba(255,255,255,0.02); padding:12px; border-radius:8px;">
            <div>
                 <strong style="color:var(--text-primary); display:block;">🎣 Hook:</strong>
                 <span style="color:var(--text-muted);">${video.hook || 'N/A'}</span>
            </div>
            <div>
                 <strong style="color:var(--text-primary); display:block;">📣 CTA:</strong>
                 <span style="color:var(--text-muted);">${video.cta || 'N/A'}</span>
            </div>
            <div>
                 <strong style="color:var(--text-primary); display:block;">🎯 Target Audience:</strong>
                 <span style="color:var(--text-muted);">${video.target_audience || 'N/A'}</span>
            </div>
            <div>
                 <strong style="color:var(--text-primary); display:block;">⚠️ Content Gap:</strong>
                 <span style="color:var(--accent-warning);">${video.content_gap || 'N/A'}</span>
            </div>
        </div>

        </div>

    </div>
    `;
}

window.createVideoCard = createVideoCard;
