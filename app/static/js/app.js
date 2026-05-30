// Global State Manager
const state = {
    activeView: 'landing',
    selectedJobType: 'send_email',
    jobs: [], // Holds all created jobs: { id, type, status, progress, payload, result }
    pollingInterval: null
};

// SVG Progress Ring calculations
const circle = document.getElementById('gauge-circle');
const radius = circle.r.baseVal.value;
const circumference = radius * 2 * Math.PI;
circle.style.strokeDasharray = `${circumference} ${circumference}`;
circle.style.strokeDashoffset = circumference;

function setProgressRing(percent) {
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
}

// Switch between SPA pages
function switchView(viewName) {
    state.activeView = viewName;
    
    // Deactivate all sections and links
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    // Activate target
    const targetSection = document.getElementById(`view-${viewName}`);
    if (targetSection) targetSection.classList.add('active');
    
    // Find active nav button
    const navButtons = document.querySelectorAll('.nav-links button');
    navButtons.forEach(btn => {
        if (btn.getAttribute('onclick').includes(viewName)) {
            btn.classList.add('active');
        }
    });

    writeTerminalLog(`[SYSTEM] Switched console viewport context to: ${viewName.toUpperCase()}`, 'info');
}

// Select active job type tab
function selectJobType(jobType) {
    state.selectedJobType = jobType;
    
    // Update tabs active state
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${jobType}`).classList.add('active');
    
    // Update hidden input
    document.getElementById('input-job-type').value = jobType;
    
    // Hide all forms, show target
    document.querySelectorAll('.form-fields').forEach(f => f.style.display = 'none');
    document.getElementById(`form-fields-${jobType}`).style.display = 'block';

    writeTerminalLog(`[CONSOLE] Selected workload schema: ${jobType.toUpperCase()}`, 'info');
}

// Write line in monospaced terminal logs widget
function writeTerminalLog(text, level = 'info') {
    const term = document.getElementById('logs-terminal');
    if (!term) return;
    
    const line = document.createElement('div');
    line.className = `log-line ${level}`;
    const timestamp = new Date().toLocaleTimeString();
    line.innerText = `[${timestamp}] ${text}`;
    
    term.appendChild(line);
    term.scrollTop = term.scrollHeight; // Auto Scroll
}

// Submit a new job to FastAPI
async def handleFormSubmit(event) {
    event.preventDefault();
    
    const jobType = state.selectedJobType;
    const payload = {};
    
    // Compile payload values based on job type
    if (jobType === 'send_email') {
        payload.email = document.getElementById('email-to').value;
        payload.subject = document.getElementById('email-subject').value;
        payload.body = document.getElementById('email-body').value;
    } else if (jobType === 'resize_image') {
        payload.image_url = document.getElementById('img-url').value;
        payload.width = parseInt(document.getElementById('img-width').value);
        payload.height = parseInt(document.getElementById('img-height').value);
    } else if (jobType === 'process_data') {
        payload.dataset_size = parseInt(document.getElementById('data-size').value);
        payload.source = document.getElementById('data-source').value;
    } else if (jobType === 'generate_report') {
        payload.report_id = document.getElementById('report-id').value;
        payload.format = document.getElementById('report-format').value;
    }
    
    writeTerminalLog(`[HTTP] Posting POST /api/jobs... Payload serialized.`, 'info');
    
    try {
        const response = await fetch('/api/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_type: jobType, payload: payload })
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Failed to queue task');
        }
        
        const data = await response.json();
        const jobId = data.job_id;
        
        writeTerminalLog(`[REDIS] Broker returned Job UUID: ${jobId}. Queued successfully.`, 'success');
        
        // Append new job to local tracker
        state.jobs.push({
            id: jobId,
            type: jobType,
            status: 'queued',
            progress: 0,
            payload: payload,
            result: null
        });
        
        // Refresh display immediately
        updateDashboardView();
        updateTimelineView();
        
        // Ensure polling active
        startPollingEngine();
        
    } catch (err) {
        writeTerminalLog(`[ERROR] Submission failed: ${err.message}`, 'error');
        alert(`Error: ${err.message}`);
    }
}

// Start polling for active jobs
function startPollingEngine() {
    if (state.pollingInterval) return;
    
    writeTerminalLog(`[SYSTEM] Initializing background polling thread... Interval = 1500ms`, 'info');
    state.pollingInterval = setInterval(async () => {
        const activeJobs = state.jobs.filter(j => j.status === 'queued' || j.status === 'processing');
        
        if (activeJobs.length === 0) {
            clearInterval(state.pollingInterval);
            state.pollingInterval = null;
            writeTerminalLog(`[SYSTEM] All queued tasks complete. Suspended polling loop.`, 'info');
            return;
        }
        
        // Poll each active job
        for (const job of activeJobs) {
            try {
                const res = await fetch(`/api/jobs/${job.id}`);
                if (!res.ok) continue;
                
                const data = await res.json();
                
                // If status changed or progress updated
                if (job.status !== data.status || job.progress !== data.progress) {
                    job.status = data.status;
                    job.progress = data.progress;
                    
                    if (data.status === 'processing') {
                        writeTerminalLog(`[CELERY] Job ${job.id.substring(0,8)}... progress updated: ${data.progress}%`, 'info');
                    }
                    
                    if (data.status === 'completed') {
                        writeTerminalLog(`[CELERY] Task ${job.id.substring(0,8)}... finished completely. Fetching outputs.`, 'success');
                        
                        // Fetch final result payload
                        const resultRes = await fetch(`/api/jobs/${job.id}/result`);
                        if (resultRes.ok) {
                            const resultData = await resultRes.json();
                            job.result = resultData.result;
                        }
                    } else if (data.status === 'failed') {
                        writeTerminalLog(`[WORKER-CRASH] Task ${job.id.substring(0,8)}... reported failure status.`, 'error');
                        job.result = data.result || { error: 'Unknown worker failure' };
                    }
                    
                    updateDashboardView();
                    updateTimelineView();
                }
            } catch (pollErr) {
                console.error(`Error polling job ${job.id}:`, pollErr);
            }
        }
    }, 1500);
}

// Update Active Queue Sidebar and Stats
function updateDashboardView() {
    // Stats calculation
    const total = state.jobs.length;
    const completed = state.jobs.filter(j => j.status === 'completed').length;
    const active = state.jobs.filter(j => j.status === 'queued' || j.status === 'processing').length;
    const successRate = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    document.getElementById('stat-total-jobs').innerText = total;
    document.getElementById('stat-completed-jobs').innerText = `${successRate}%`;
    document.getElementById('stat-active-jobs').innerText = active;
    
    // Update SVG progress ring
    setProgressRing(successRate);
    document.getElementById('gauge-percentage-text').innerHTML = `${successRate}% <span>Success</span>`;
    
    // Update active tasks panel list
    const activeTasksList = document.getElementById('active-tasks-list');
    document.getElementById('queue-counter').innerText = `${active} Jobs`;
    
    if (active === 0) {
        activeTasksList.innerHTML = `
            <div style="text-align: center; color: var(--text-secondary); padding: 4rem 1rem; font-size: 0.9rem;">
                No active tasks running.<br>Use the console on the left to submit a job!
            </div>`;
        return;
    }
    
    activeTasksList.innerHTML = '';
    state.jobs.filter(j => j.status === 'queued' || j.status === 'processing').forEach(job => {
        const item = document.createElement('div');
        item.className = 'mini-task-item';
        item.onclick = () => { switchView('timeline'); toggleTimelineDetails(job.id); };
        
        item.innerHTML = `
            <div class="mini-task-header">
                <span class="mini-task-type">${job.type}</span>
                <span class="badge ${job.status}">${job.status}</span>
            </div>
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-secondary);">
                ID: ${job.id.substring(0,18)}...
            </div>
            <div class="progress-bar-bg" style="margin-top: 0.25rem;">
                <div class="progress-bar-fill" style="width: ${job.progress}%"></div>
            </div>
            <div style="font-size: 0.75rem; color: var(--text-secondary); text-align: right;">
                ${job.progress}%
            </div>
        `;
        activeTasksList.appendChild(item);
    });
}

// Update Timeline Manager View
function updateTimelineView() {
    const list = document.getElementById('historical-timeline-list');
    if (!list) return;
    
    if (state.jobs.length === 0) {
        list.innerHTML = `
            <div class="glass-panel" style="padding: 4rem; text-align: center; color: var(--text-secondary);">
                <div style="font-size: 2rem; margin-bottom: 1rem;">📥</div>
                <h4>No Job Submissions Registered</h4>
                <p style="font-size: 0.9rem; margin-top: 0.5rem; max-width: 400px; margin-left: auto; margin-right: auto;">Go to the "Console Dashboard" tab and submit standard email, resizing or report generation jobs to populate this registry.</p>
            </div>`;
        return;
    }
    
    list.innerHTML = '';
    
    // Sort in reverse chronological order (newest first)
    [...state.jobs].reverse().forEach(job => {
        const item = document.createElement('div');
        item.className = 'timeline-item glass-panel';
        item.id = `timeline-item-${job.id}`;
        
        const typeIcons = {
            send_email: '✉️',
            resize_image: '🖼️',
            process_data: '📊',
            generate_report: '📄'
        };
        
        item.innerHTML = `
            <div class="timeline-header-row">
                <div class="timeline-icon-box">
                    ${typeIcons[job.type] || '⚙️'}
                </div>
                <div class="timeline-details">
                    <h3>${job.type}</h3>
                    <span class="task-uuid">UUID: ${job.id}</span>
                </div>
                <div class="timeline-progress-cell">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge ${job.status}">${job.status}</span>
                        <span class="progress-text">${job.progress}%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${job.progress}%"></div>
                    </div>
                </div>
                <button class="toggle-details-btn" id="btn-toggle-${job.id}" onclick="toggleTimelineDetails('${job.id}')">
                    ▼
                </button>
            </div>
            
            <div class="timeline-expandable-details" id="details-${job.id}">
                <div class="json-block-container">
                    <h5>Task Ingest Input Payload</h5>
                    <pre class="json-block">${JSON.stringify(job.payload, null, 2)}</pre>
                </div>
                <div class="json-block-container">
                    <h5>Task Output Metadata</h5>
                    <pre class="json-block">${job.result ? JSON.stringify(job.result, null, 2) : (job.status === 'failed' ? 'Task execution raised an exception.' : 'Task outputs will display here once completed.')}</pre>
                </div>
            </div>
        `;
        list.appendChild(item);
    });
}

// Toggle Expanded timeline card
function toggleTimelineDetails(jobId) {
    const details = document.getElementById(`details-${jobId}`);
    const btn = document.getElementById(`btn-toggle-${jobId}`);
    
    if (details.classList.contains('open')) {
        details.classList.remove('open');
        btn.classList.remove('open');
    } else {
        details.classList.add('open');
        btn.classList.add('open');
    }
}

// Clear historic entries
function clearAllHistoricalTasks() {
    state.jobs = [];
    updateDashboardView();
    updateTimelineView();
    writeTerminalLog('[SYSTEM] Flushed all job execution history cache from viewport memory.', 'warn');
}

// Initialize viewport on load
document.addEventListener('DOMContentLoaded', () => {
    switchView('landing');
    selectJobType('send_email');
});
