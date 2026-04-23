// AgentLens Frontend
const API = ''; // relative URL, served by FastAPI

let testCases = [];
let agentConfigs = [];
let runs = [];

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    checkServerStatus();
    loadTestCases();
    loadAgentConfigs();
    loadStats();
});

// --- Tabs ---
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            const panelId = `panel-${tab.dataset.tab}`;
            document.getElementById(panelId).classList.add('active');
            if (tab.dataset.tab === 'results') loadResults();
            if (tab.dataset.tab === 'stats') loadStats();
            if (tab.dataset.tab === 'run-tests') loadTestCasesForRun();
            if (tab.dataset.tab === 'configs') loadAgentConfigs();
        });
    });
}

// --- Server Status ---
async function checkServerStatus() {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    try {
        const res = await fetch(`${API}/api/stats`);
        if (res.ok) {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
            return;
        }
    } catch (e) {}
    dot.className = 'status-dot error';
    text.textContent = 'Disconnected';
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleString('en-IN', { 
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    });
}

// --- Test Cases ---
async function loadTestCases() {
    try {
        const res = await fetch(`${API}/api/test-cases`);
        testCases = await res.json();
        renderTestCases();
    } catch (e) {
        console.error('Failed to load test cases', e);
    }
}

function renderTestCases() {
    const list = document.getElementById('test-cases-list');
    if (testCases.length === 0) {
        list.innerHTML = '<div class="empty-state">No test cases yet. Create one to get started.</div>';
        return;
    }
    list.innerHTML = testCases.map(tc => `
        <div class="card-item" onclick="showTestDetail(${tc.id})">
            <div class="card-item-header">
                <span class="card-item-title">${escapeHtml(tc.name)}</span>
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deleteTestCase(${tc.id})">Delete</button>
            </div>
            ${tc.description ? `<div class="card-item-desc">${escapeHtml(tc.description)}</div>` : ''}
            <div class="card-item-meta">
                <span>${tc.expected_keywords ? 'Keywords: ' + tc.expected_keywords : 'No keywords'}</span>
                <span>${formatDate(tc.created_at)}</span>
            </div>
        </div>
    `).join('');
}

async function createTestCase(e) {
    e.preventDefault();
    const data = {
        name: document.getElementById('tc-name').value,
        description: document.getElementById('tc-description').value,
        input_prompt: document.getElementById('tc-prompt').value,
        expected_keywords: document.getElementById('tc-keywords').value,
        system_prompt: document.getElementById('tc-system').value || "You are a helpful AI assistant."
    };
    try {
        const res = await fetch(`${API}/api/test-cases`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        hideModal('modal-create-test');
        document.getElementById('form-create-test').reset();
        await loadTestCases();
    } catch (e) {
        alert('Failed to create test case: ' + e.message);
    }
}

async function deleteTestCase(id) {
    if (!confirm('Delete this test case and all its runs?')) return;
    try {
        await fetch(`${API}/api/test-cases/${id}`, { method: 'DELETE' });
        await loadTestCases();
        await loadStats();
    } catch (e) {
        alert('Failed to delete: ' + e.message);
    }
}

function showTestDetail(id) {
    const tc = testCases.find(t => t.id === id);
    if (!tc) return;
    const html = `
        <div class="run-detail-section">
            <h4>Input Prompt</h4>
            <pre>${escapeHtml(tc.input_prompt)}</pre>
        </div>
        ${tc.expected_keywords ? `
        <div class="run-detail-section">
            <h4>Expected Keywords</h4>
            <pre>${escapeHtml(tc.expected_keywords)}</pre>
        </div>` : ''}
        ${tc.system_prompt ? `
        <div class="run-detail-section">
            <h4>System Prompt</h4>
            <pre>${escapeHtml(tc.system_prompt)}</pre>
        </div>` : ''}
    `;
    document.getElementById('run-detail-content').innerHTML = html;
    document.getElementById('modal-run-detail').classList.remove('hidden');
}

// --- Run Tests ---
function loadTestCasesForRun() {
    const select = document.getElementById('run-test-cases-select');
    if (testCases.length === 0) {
        select.innerHTML = '<div class="text-muted" style="padding:12px">No test cases available. Create some first.</div>';
        return;
    }
    select.innerHTML = testCases.map(tc => `
        <label class="checkbox-item">
            <input type="checkbox" value="${tc.id}" checked>
            <span>${escapeHtml(tc.name)}</span>
        </label>
    `).join('');
}

async function runSelectedTests() {
    const checkboxes = document.querySelectorAll('#run-test-cases-select input[type="checkbox"]:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    if (selectedIds.length === 0) {
        alert('Select at least one test case');
        return;
    }
    const apiUrl = document.getElementById('run-api-url').value;
    const apiKey = document.getElementById('run-api-key').value;
    const model = document.getElementById('run-model').value;
    
    if (!apiKey) {
        alert('Please enter an API key');
        return;
    }

    const progress = document.getElementById('run-progress');
    const count = document.getElementById('run-progress-count');
    const fill = document.getElementById('progress-fill');
    const preview = document.getElementById('run-results-preview');
    
    progress.classList.remove('hidden');
    preview.innerHTML = '';
    
    let completed = 0;
    const results = [];
    
    for (const id of selectedIds) {
        count.textContent = `${completed}/${selectedIds.length}`;
        const pct = (completed / selectedIds.length) * 100;
        fill.style.width = `${pct}%`;
        
        // Add pending item
        const itemId = `run-item-${id}`;
        preview.innerHTML += `<div id="${itemId}" class="result-item" style="opacity:0.5">
            <div class="result-item-header">
                <span class="result-item-name">Running test #${id}...</span>
            </div>
        </div>`;
        
        try {
            const res = await fetch(`${API}/api/runs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ test_case_id: id, api_url: apiUrl, api_key: apiKey, model })
            });
            const result = await res.json();
            results.push(result);
            
            const tc = testCases.find(t => t.id === id);
            const statusBadge = result.status === 'passed' ? 'badge-passed' : result.status === 'failed' ? 'badge-failed' : 'badge-error';
            
            document.getElementById(itemId).outerHTML = `
                <div class="result-item" onclick="showRunDetail(${result.id})">
                    <div class="result-item-header">
                        <span class="result-item-name">${escapeHtml(tc?.name || 'Test #'+id)}</span>
                        <span class="badge ${statusBadge}">${result.status}</span>
                    </div>
                    <div class="result-item-meta">
                        <span>${result.model}</span>
                        <span>${result.duration_ms}ms</span>
                        <span>${formatDate(result.created_at)}</span>
                    </div>
                    ${result.error ? `<div class="result-preview text-red">Error: ${escapeHtml(result.error)}</div>` : ''}
                </div>
            `;
        } catch (e) {
            document.getElementById(itemId).outerHTML = `
                <div class="result-item">
                    <div class="result-item-header">
                        <span class="result-item-name">Test #${id}</span>
                        <span class="badge badge-error">Error</span>
                    </div>
                    <div class="result-preview text-red">${escapeHtml(e.message)}</div>
                </div>
            `;
        }
        
        completed++;
        count.textContent = `${completed}/${selectedIds.length}`;
        fill.style.width = `${(completed / selectedIds.length) * 100}%`;
    }
    
    // Refresh stats
    loadStats();
}

// --- Results ---
async function loadResults() {
    const filter = document.getElementById('results-filter')?.value || '';
    try {
        const res = await fetch(`${API}/api/runs?limit=100`);
        runs = await res.json();
        
        const filtered = filter ? runs.filter(r => r.status === filter) : runs;
        
        const list = document.getElementById('results-list');
        if (filtered.length === 0) {
            list.innerHTML = '<div class="empty-state">No test runs yet.</div>';
            return;
        }
        
        list.innerHTML = filtered.map(r => {
            const statusBadge = r.status === 'passed' ? 'badge-passed' : r.status === 'failed' ? 'badge-failed' : 'badge-error';
            const preview = r.error ? `Error: ${escapeHtml(r.error)}` : (r.output || '').slice(0, 200);
            return `
                <div class="result-item" onclick="showRunDetail(${r.id})">
                    <div class="result-item-header">
                        <span class="result-item-name">${escapeHtml(r.test_name || 'Test')}</span>
                        <span class="badge ${statusBadge}">${r.status}</span>
                    </div>
                    <div class="result-item-meta">
                        <span>${r.model || 'unknown'}</span>
                        <span>${r.duration_ms ? r.duration_ms + 'ms' : ''}</span>
                        <span>${formatDate(r.created_at)}</span>
                    </div>
                    <div class="result-preview">${escapeHtml(preview)}</div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Failed to load results', e);
    }
}

async function showRunDetail(runId) {
    try {
        const res = await fetch(`${API}/api/runs/${runId}`);
        const r = await res.json();
        
        const statusBadge = r.status === 'passed' ? 'badge-passed' : r.status === 'failed' ? 'badge-failed' : 'badge-error';
        const errorSection = r.error ? `
            <div class="run-detail-section">
                <h4>Error</h4>
                <pre class="text-red">${escapeHtml(r.error)}</pre>
            </div>
        ` : '';
        
        const html = `
            <div class="run-detail-header">
                <span class="badge ${statusBadge}" style="font-size:14px;padding:6px 14px">${r.status}</span>
                <span class="text-muted">${r.test_name || 'Test Run'}</span>
            </div>
            <div class="run-detail-meta">
                <div class="run-detail-meta-item">
                    <div class="label">Model</div>
                    <div class="value">${r.model || 'N/A'}</div>
                </div>
                <div class="run-detail-meta-item">
                    <div class="label">Duration</div>
                    <div class="value">${r.duration_ms ? r.duration_ms + 'ms' : 'N/A'}</div>
                </div>
                <div class="run-detail-meta-item">
                    <div class="label">Date</div>
                    <div class="value">${formatDate(r.created_at)}</div>
                </div>
            </div>
            <div class="run-detail-section">
                <h4>Input Prompt</h4>
                <pre>${escapeHtml(r.input_prompt || '')}</pre>
            </div>
            ${r.expected_keywords ? `
            <div class="run-detail-section">
                <h4>Expected Keywords</h4>
                <pre>${escapeHtml(r.expected_keywords)}</pre>
            </div>` : ''}
            <div class="run-detail-section">
                <h4>Agent Output</h4>
                <pre>${escapeHtml(r.output || '')}</pre>
            </div>
            ${errorSection}
        `;
        
        document.getElementById('run-detail-content').innerHTML = html;
        document.getElementById('modal-run-detail').classList.remove('hidden');
    } catch (e) {
        console.error('Failed to load run detail', e);
    }
}

// --- Agent Configs ---
async function loadAgentConfigs() {
    try {
        const res = await fetch(`${API}/api/agent-configs`);
        agentConfigs = await res.json();
        renderAgentConfigs();
    } catch (e) {
        console.error('Failed to load configs', e);
    }
}

function renderAgentConfigs() {
    const list = document.getElementById('configs-list');
    if (agentConfigs.length === 0) {
        list.innerHTML = '<div class="empty-state">No agent configs saved. Create one for quick test runs.</div>';
        return;
    }
    list.innerHTML = agentConfigs.map(cfg => `
        <div class="card-item">
            <div class="card-item-header">
                <span class="card-item-title">${escapeHtml(cfg.name)}</span>
                <button class="btn btn-danger btn-sm" onclick="deleteAgentConfig(${cfg.id})">Delete</button>
            </div>
            <div class="card-item-meta">
                <span>${cfg.api_url}</span>
                <span>${cfg.model}</span>
                <span>${formatDate(cfg.created_at)}</span>
            </div>
        </div>
    `).join('');
}

async function createAgentConfig(e) {
    e.preventDefault();
    const data = {
        name: document.getElementById('cfg-name').value,
        api_url: document.getElementById('cfg-api-url').value,
        api_key: document.getElementById('cfg-api-key').value,
        model: document.getElementById('cfg-model').value
    };
    try {
        const res = await fetch(`${API}/api/agent-configs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        hideModal('modal-create-config');
        document.getElementById('form-create-config').reset();
        await loadAgentConfigs();
    } catch (e) {
        alert('Failed to create config: ' + e.message);
    }
}

async function deleteAgentConfig(id) {
    if (!confirm('Delete this config?')) return;
    try {
        await fetch(`${API}/api/agent-configs/${id}`, { method: 'DELETE' });
        await loadAgentConfigs();
    } catch (e) {
        alert('Failed to delete: ' + e.message);
    }
}

// --- Stats ---
async function loadStats() {
    try {
        const res = await fetch(`${API}/api/stats`);
        const s = await res.json();
        
        document.getElementById('stat-total-cases').textContent = s.total_cases;
        document.getElementById('stat-total-runs').textContent = s.total_runs;
        document.getElementById('stat-passed').textContent = s.passed;
        document.getElementById('stat-failed').textContent = s.failed;
        document.getElementById('stat-errors').textContent = s.errors;
        document.getElementById('stat-pass-rate').textContent = s.pass_rate + '%';
        
        const bar = document.getElementById('pass-rate-fill');
        bar.style.width = `${s.pass_rate}%`;
    } catch (e) {
        console.error('Failed to load stats', e);
    }
}

// --- Modal Helpers ---
function showCreateTestModal() {
    document.getElementById('modal-create-test').classList.remove('hidden');
}
function showCreateConfigModal() {
    document.getElementById('modal-create-config').classList.remove('hidden');
}
function hideModal(id) {
    document.getElementById(id).classList.add('hidden');
}

// --- Utilities ---
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Close modals on escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal:not(.hidden)').forEach(m => m.classList.add('hidden'));
    }
});

// Close modals on backdrop click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
        }
    });
});