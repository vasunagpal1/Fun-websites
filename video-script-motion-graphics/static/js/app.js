/**
 * MotionScript – Client-side app logic
 */

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

// ── State ────────────────────────────────────────────────────────────────────

let state = {
    script: '',
    numSegments: 4,
    duration: 5,
    segments: [],
    jobId: null,
};

// ── Step Navigation ──────────────────────────────────────────────────────────

function showStep(id) {
    $$('.step').forEach(s => s.classList.remove('active'));
    $(`#${id}`).classList.add('active');
}

// ── Toggle Buttons ───────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Segments toggle
    $$('.control-group:nth-child(1) .toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            $$('.control-group:nth-child(1) .toggle').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.numSegments = parseInt(btn.dataset.value);
        });
    });

    // Duration toggle
    $$('.control-group:nth-child(2) .toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            $$('.control-group:nth-child(2) .toggle').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.duration = parseFloat(btn.dataset.value);
        });
    });
});

// ── Analyze ──────────────────────────────────────────────────────────────────

$('#btn-analyze').addEventListener('click', async () => {
    const script = $('#script-input').value.trim();
    if (!script) return;

    state.script = script;
    const btn = $('#btn-analyze');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script: state.script,
                num_segments: state.numSegments,
            }),
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        state.segments = data.segments;
        renderSegments(data.segments);
        showStep('step-preview');
    } catch (err) {
        alert('Analysis failed: ' + err.message);
    } finally {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

function renderSegments(segments) {
    const list = $('#segments-list');
    list.innerHTML = segments.map((seg, i) => `
        <div class="segment-card">
            <div class="segment-meta">
                <div class="segment-num ${seg.category}">${seg.index}</div>
                <span class="segment-badge">${seg.category}</span>
                <span class="segment-score">score: ${seg.score}</span>
            </div>
            <p class="segment-text">${escapeHtml(seg.text)}</p>
        </div>
    `).join('');
}

// ── Back ─────────────────────────────────────────────────────────────────────

$('#btn-back').addEventListener('click', () => showStep('step-input'));

// ── Generate ─────────────────────────────────────────────────────────────────

$('#btn-generate').addEventListener('click', async () => {
    const btn = $('#btn-generate');
    btn.classList.add('loading');
    btn.disabled = true;

    try {
        const res = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                script: state.script,
                num_segments: state.numSegments,
                duration: state.duration,
            }),
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);

        state.jobId = data.job_id;
        showStep('step-generating');
        pollStatus();
    } catch (err) {
        alert('Generation failed: ' + err.message);
        btn.classList.remove('loading');
        btn.disabled = false;
    }
});

async function pollStatus() {
    const fill = $('#progress-fill');
    const text = $('#progress-text');
    let elapsed = 0;

    const interval = setInterval(async () => {
        elapsed += 1;
        try {
            const res = await fetch(`/api/status/${state.jobId}`);
            const data = await res.json();

            text.textContent = data.progress;

            if (data.status === 'running') {
                // Estimate progress (rendering is the bottleneck)
                const estimatedTotal = state.numSegments * state.duration * 3;
                const pct = Math.min(95, (elapsed / estimatedTotal) * 100);
                fill.style.width = pct + '%';
            } else if (data.status === 'done') {
                clearInterval(interval);
                fill.style.width = '100%';
                setTimeout(() => renderResults(data.result), 500);
            } else if (data.status === 'error') {
                clearInterval(interval);
                fill.style.width = '0%';
                text.textContent = 'Error: ' + data.progress;
                text.style.color = 'var(--danger)';
            }
        } catch {
            // Network hiccup, keep polling
        }
    }, 1000);
}

function renderResults(result) {
    showStep('step-results');
    const grid = $('#results-grid');
    let html = '';

    // Combined video first
    if (result.combined) {
        html += `
            <div class="result-card combined">
                <div class="result-header">
                    <span class="result-title">Combined Video</span>
                    <span class="result-badge combined">Full Cut</span>
                </div>
                <video class="preview" controls preload="metadata"
                       src="/output/${state.jobId}/${result.combined}"></video>
                <div class="result-desc">All ${result.clips.length} motion graphics combined into one seamless video.</div>
                <div class="result-actions">
                    <a class="btn btn-primary" href="/output/${state.jobId}/${result.combined}" download>
                        Download Combined MP4
                    </a>
                </div>
            </div>
        `;
    }

    // Individual clips
    result.segments.forEach((seg, i) => {
        const clipFile = result.clips[i];
        if (!clipFile) return;
        html += `
            <div class="result-card">
                <div class="result-header">
                    <span class="result-title">Clip ${i + 1} — ${seg.category}</span>
                    <span class="result-badge clip">${seg.category}</span>
                </div>
                <video class="preview" controls preload="metadata"
                       src="/output/${state.jobId}/${clipFile}"></video>
                <div class="result-desc">${escapeHtml(seg.text)}</div>
                <div class="result-actions">
                    <a class="btn btn-ghost" href="/output/${state.jobId}/${clipFile}" download>
                        Download Clip
                    </a>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;
}

// ── New Script ───────────────────────────────────────────────────────────────

$('#btn-new').addEventListener('click', () => {
    $('#script-input').value = '';
    state = { script: '', numSegments: 4, duration: 5, segments: [], jobId: null };
    showStep('step-input');
});

// ── Util ─────────────────────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
