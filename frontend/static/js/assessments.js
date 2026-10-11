const $ = id => document.getElementById(id);
let attempt = null;
let timerHandle = null;
let secondsLeft = 900;
let faceModel = null;
let cocoModel = null;
let cameraStream = null;
let monitorHandle = null;
let violations = 0;
let submitting = false;
const lastEventAt = Object.create(null);
const EVENT_COOLDOWN_MS = 8000;

async function api(path, opts = {}) {
    const r = await fetch(path, {
        ...opts,
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) }
    });
    const d = await r.json().catch(() => ({ message: 'Unexpected server response' }));
    if (!r.ok) throw new Error(d.message || `Request failed (${r.status})`);
    return d;
}

function esc(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function status(s) {
    const el = $('proctorStatus');
    if (el) el.textContent = s;
}

async function recordProctorEvent(type, details = '') {
    if (!attempt) return;
    const now = Date.now();
    if (lastEventAt[type] && now - lastEventAt[type] < EVENT_COOLDOWN_MS) return;
    lastEventAt[type] = now;

    try {
        const result = await api(`/api/assessments/${attempt.attempt_id}/proctor-event`, {
            method: 'POST',
            body: JSON.stringify({ event_type: type, details })
        });
        violations = result.violations ?? violations;
        if (result.terminate) {
            status('Assessment terminated after 3 or more proctoring violations.');
            await submit(true, 'PROCTOR_VIOLATION');
        }
    } catch (e) {
        console.warn('Proctor event was not recorded', e);
    }
}

async function startCamera() {
    try {
        if (!navigator.mediaDevices?.getUserMedia) throw new Error('Camera API unavailable in this browser.');
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
        const video = $('cameraPreview');
        if (video) {
            video.srcObject = cameraStream;
            await video.play();
        }
        status('Camera active. Keep only yourself in frame and phones away from the workspace.');
        await loadModels();
        monitorHandle = setInterval(scanCamera, 1800);
    } catch (e) {
        status('Camera unavailable: ' + e.message);
        await recordProctorEvent('CAMERA_PERMISSION_DENIED', e.message);
    }
}

async function loadModels() {
    try {
        if (!window.blazeface || !window.cocoSsd) {
            throw new Error('AI detection libraries not loaded yet.');
        }
        faceModel = await blazeface.load();
        cocoModel = await cocoSsd.load();
        status('AI camera monitoring active: BlazeFace & COCO-SSD checks enabled.');
    } catch (e) {
        status('Camera is active, but AI model loading was skipped: ' + e.message);
        await recordProctorEvent('CAMERA_UNAVAILABLE', e.message);
    }
}

async function scanCamera() {
    if (!attempt || !faceModel || !cocoModel) return;
    const video = $('cameraPreview');
    if (!video || video.readyState < 2) return;

    try {
        const faces = await faceModel.estimateFaces(video, false);
        if (faces.length > 1) {
            status(`Multiple faces detected (${faces.length}). Ensure you are alone.`);
            await recordProctorEvent('MULTIPLE_FACES', `${faces.length} faces detected`);
        }

        const objects = await cocoModel.detect(video);
        const phones = objects.filter(o => o.class === 'cell phone' && o.score >= 0.55);
        if (phones.length) {
            status('Mobile phone detected in frame. Remove it immediately.');
            await recordProctorEvent('MOBILE_DETECTED', `confidence=${phones[0].score.toFixed(2)}`);
        }
    } catch (e) {
        console.debug('Camera inference issue', e);
    }
}

async function cleanup() {
    if (timerHandle) clearInterval(timerHandle);
    if (monitorHandle) clearInterval(monitorHandle);
    if (cameraStream) {
        cameraStream.getTracks().forEach(t => t.stop());
        cameraStream = null;
    }
}

async function load() {
    try {
        const rows = await api('/api/assessments/available');
        const el = $('assessmentList');
        if (!rows.length) {
            el.innerHTML = '<p class="muted" style="padding: 16px;">Save at least one skill in your Candidate Profile to access its skill assessment.</p>';
            return;
        }

        el.innerHTML = rows.map(s => `
            <article class="assessment-item">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                    <div>
                        <h3 style="margin: 0 0 6px 0;">${esc(s.name)}</h3>
                        <p class="muted" style="margin: 0;">
                            ${s.question_count} questions in bank · 
                            ${s.best_percentage === null ? 'Not yet assessed' : `<strong style="color: var(--secondary);">Best result: ${Number(s.best_percentage).toFixed(1)}%</strong>`}
                        </p>
                    </div>
                    <button class="primary-btn" data-skill="${s.skill_id}" style="padding: 10px 22px;">
                        Start 50-Mark Assessment
                    </button>
                </div>
            </article>
        `).join('');

        el.querySelectorAll('button[data-skill]').forEach(b => {
            b.addEventListener('click', () => start(Number(b.dataset.skill)));
        });
    } catch (e) {
        $('assessmentList').textContent = e.message;
    }
}

async function start(skillId) {
    try {
        const data = await api('/api/assessments/start', {
            method: 'POST',
            body: JSON.stringify({ skill_id: skillId })
        });

        attempt = data;
        violations = 0;
        $('assessmentPicker').hidden = true;
        $('testArea').hidden = false;
        $('testTitle').textContent = `${data.skill} Assessment`;

        const summary = $('assessmentRules');
        if (summary) {
            summary.textContent = '10 questions · Easy 3×3 marks, Medium 4×5 marks, Hard 3×7 marks · Total 50 Marks · 15 Minutes';
        }

        $('questions').innerHTML = data.questions.map(q => {
            const diff = String(q.difficulty || 'medium').toUpperCase();
            return `
                <article class="assessment-item">
                    <span class="qmeta">${esc(diff)} · ${q.marks} MARKS</span>
                    <h3>${q.number}. ${esc(q.text)}</h3>
                    ${Object.entries(q.options).map(([k, v]) => `
                        <label>
                            <input type="radio" name="q_${q.id}" value="${k}"> 
                            <strong>${k}.</strong> ${esc(v)}
                        </label>
                    `).join('')}
                </article>
            `;
        }).join('');

        secondsLeft = data.time_limit_seconds || 900;
        updateTimer();
        timerHandle = setInterval(() => {
            secondsLeft--;
            updateTimer();
            if (secondsLeft <= 0) {
                submit(true, 'TIME_EXPIRED');
            }
        }, 1000);

        await startCamera();

        try {
            if (document.documentElement.requestFullscreen) {
                await document.documentElement.requestFullscreen();
            }
        } catch (e) {
            await recordProctorEvent('FULLSCREEN_EXIT', 'Could not enter fullscreen mode');
        }
    } catch (e) {
        alert(e.message);
    }
}

function updateTimer() {
    const m = String(Math.max(0, Math.floor(secondsLeft / 60))).padStart(2, '0');
    const s = String(Math.max(0, secondsLeft % 60)).padStart(2, '0');
    const timerEl = $('timer');
    if (timerEl) timerEl.textContent = `${m}:${s}`;
}

async function submit(expired = false, reason = 'MANUAL') {
    if (!attempt || submitting) return;
    submitting = true;

    const btn = $('testForm').querySelector('button[type=submit]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Grading & Submitting...';
    }

    const answers = {};
    attempt.questions.forEach(q => {
        const selected = document.querySelector(`input[name="q_${q.id}"]:checked`);
        if (selected) answers[q.id] = selected.value;
    });

    try {
        const result = await api(`/api/assessments/${attempt.attempt_id}/submit`, {
            method: 'POST',
            body: JSON.stringify({ answers, reason })
        });

        await cleanup();

        if (document.fullscreenElement) {
            try { await document.exitFullscreen(); } catch (e) {}
        }

        $('testArea').hidden = true;
        $('result').hidden = false;

        const pct = Number(result.percentage || 0);
        const grade = pct >= 80 ? 'Excellent (Tier 1 Verified)' : (pct >= 60 ? 'Good (Proficient)' : (pct >= 40 ? 'Needs Practice' : 'Developing'));
        const isTerminated = result.status === 'TERMINATED';

        $('result').innerHTML = `
            <h2>${isTerminated ? 'Assessment Terminated' : 'Assessment Completed'}</h2>
            <p>Status: <strong style="color: ${isTerminated ? '#ff3366' : 'var(--secondary)'};">${esc(result.status)}</strong></p>
            <p style="font-size: 20px;"><strong>Score: ${result.score} / ${result.total_marks} (${pct.toFixed(1)}%)</strong></p>
            <p>Correct Answers: <strong>${result.correct_count} / 10</strong></p>
            <p>Evaluation Tier: <strong>${grade}</strong></p>
            <p class="muted">${esc(result.message)}</p>
            <a href="/candidate/dashboard">Return to Dashboard</a>
        `;

        attempt = null;
    } catch (e) {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Submit Assessment';
        }
        submitting = false;
        alert(e.message);
    }
}

$('testForm').addEventListener('submit', e => {
    e.preventDefault();
    if (confirm('Submit this assessment? Your answers will be graded immediately on the server.')) {
        submit(false, 'MANUAL');
    }
});

document.addEventListener('visibilitychange', () => {
    if (attempt && document.hidden) {
        status('⚠ WARNING: Tab switch detected. This violation is logged.');
        recordProctorEvent('TAB_SWITCH', 'Document became hidden');
    }
});

window.addEventListener('blur', () => {
    if (attempt) {
        status('⚠ WARNING: Assessment window lost focus.');
        recordProctorEvent('TAB_SWITCH', 'Window blur event');
    }
});

document.addEventListener('fullscreenchange', () => {
    if (attempt && !document.fullscreenElement) {
        status('⚠ WARNING: Fullscreen exited. This violation is logged.');
        recordProctorEvent('FULLSCREEN_EXIT', 'Fullscreen exited');
    }
});

window.addEventListener('beforeunload', e => {
    if (attempt) {
        e.preventDefault();
        e.returnValue = 'Assessment in progress';
    }
});

load();