// TalentPulse AI — Minimal Vanilla JavaScript Client
let state = {
  token: localStorage.getItem("tp_token") || null,
  user: null,
  activeTab: "tab-home",
  teamEmployees: [],
  selectedReviewEmployeeId: null
};

const API_BASE = "";

// ---------------------------------------------------------------------
// API Request Helper
// ---------------------------------------------------------------------
async function api(endpoint, options = {}) {
  const headers = options.headers || {};
  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (res.status === 401) {
    logout();
    throw new Error("Session expired. Please log in again.");
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const errorMsg = data && data.detail ? (typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail)) : "Request failed";
    throw new Error(errorMsg);
  }
  return data;
}

// ---------------------------------------------------------------------
// Auth & Initialization
// ---------------------------------------------------------------------
function fillLogin(email, password) {
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = password;
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  const errorEl = document.getElementById("login-error");
  errorEl.style.display = "none";

  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });
    state.token = data.access_token;
    localStorage.setItem("tp_token", state.token);
    await initApp();
  } catch (err) {
    errorEl.textContent = err.message;
    errorEl.style.display = "block";
  }
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem("tp_token");
  document.getElementById("login-container").style.display = "block";
  document.getElementById("app-container").style.display = "none";
  document.getElementById("user-bar").style.display = "none";
}

async function initApp() {
  if (!state.token) {
    document.getElementById("login-container").style.display = "block";
    document.getElementById("app-container").style.display = "none";
    document.getElementById("user-bar").style.display = "none";
    return;
  }

  try {
    state.user = await api("/auth/me");
    renderUserBar();
    applyRolePermissions();
    document.getElementById("login-container").style.display = "none";
    document.getElementById("app-container").style.display = "block";
    switchTab("tab-home");
  } catch (err) {
    logout();
  }
}

function renderUserBar() {
  const bar = document.getElementById("user-bar");
  bar.style.display = "flex";
  document.getElementById("user-name").textContent = state.user.full_name;
  const badge = document.getElementById("user-role-badge");
  badge.textContent = state.user.role;
  badge.className = `role-badge role-${state.user.role.toLowerCase()}`;
  const deptName = state.user.department ? state.user.department.name : "";
  document.getElementById("user-dept").textContent = deptName ? `• ${deptName}` : "";
}

function applyRolePermissions() {
  const role = state.user.role.toLowerCase();
  const isManagerOrAbove = ["admin", "hr", "manager"].includes(role);
  const isHROrAdmin = ["admin", "hr"].includes(role);

  // Tabs visibility
  document.querySelectorAll(".tab-manager-only").forEach(el => {
    el.style.display = isManagerOrAbove ? "block" : "none";
  });
  document.querySelectorAll(".tab-hr-only").forEach(el => {
    el.style.display = isHROrAdmin ? "block" : "none";
  });

  // Action cards visibility
  document.getElementById("team-leaves-card").style.display = isManagerOrAbove ? "block" : "none";
  document.getElementById("conduct-review-card").style.display = isManagerOrAbove ? "block" : "none";
  document.getElementById("policy-upload-card").style.display = isHROrAdmin ? "block" : "none";
  document.getElementById("employee-onboarding-card").style.display = (role === "employee") ? "block" : "none";
}

// ---------------------------------------------------------------------
// Tab Switching
// ---------------------------------------------------------------------
function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));

  const target = document.getElementById(tabId);
  if (target) target.style.display = "block";

  // Active button
  const btns = document.querySelectorAll(".tab-btn");
  btns.forEach(btn => {
    if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(tabId)) {
      btn.classList.add("active");
    }
  });

  // Load tab-specific data
  if (tabId === "tab-home") loadDashboardData();
  else if (tabId === "tab-leave") loadLeaveData();
  else if (tabId === "tab-reviews") loadReviewsData();
  else if (tabId === "tab-helpdesk") loadChatHistory();
  else if (tabId === "tab-attrition") loadAttritionData();
  else if (tabId === "tab-flags") loadPerformanceFlags();
  else if (tabId === "tab-metrics") loadAdminMetrics();
  else if (tabId === "tab-org") loadOrgData();
}

// ---------------------------------------------------------------------
// Tab 1: Dashboard
// ---------------------------------------------------------------------
async function loadDashboardData() {
  const role = state.user.role.toLowerCase();
  const kpiRow = document.getElementById("home-kpi-row");

  let kpiHtml = "";
  if (role === "employee") {
    const myLeaves = await api("/leave/my").catch(() => []);
    const pendingCount = myLeaves.filter(l => l.status === "PENDING").length;
    kpiHtml = `
      <div class="kpi-card"><div class="kpi-label">My Applied Leaves</div><div class="kpi-value">${myLeaves.length}</div></div>
      <div class="kpi-card"><div class="kpi-label">Pending Approval</div><div class="kpi-value">${pendingCount}</div></div>
      <div class="kpi-card"><div class="kpi-label">Location Center</div><div class="kpi-value" style="font-size: 1.2rem;">Vizag Tech Park</div></div>
    `;
    if (state.user.employee_id) {
      loadOnboardingTasks(state.user.employee_id);
    }
  } else if (role === "manager") {
    const teamLeaves = await api("/leave/team").catch(() => []);
    const pendingApprovals = teamLeaves.filter(l => l.status === "PENDING").length;
    const teamAttrition = await api("/attrition/team").catch(() => ({ team_size: 0, risk_counts: { HIGH: 0 } }));
    kpiHtml = `
      <div class="kpi-card"><div class="kpi-label">Direct Reports</div><div class="kpi-value">${teamAttrition.team_size}</div></div>
      <div class="kpi-card"><div class="kpi-label">Pending Leave Approvals</div><div class="kpi-value" style="color: var(--warning);">${pendingApprovals}</div></div>
      <div class="kpi-card"><div class="kpi-label">Team Attrition Risk (High)</div><div class="kpi-value" style="color: var(--danger);">${teamAttrition.risk_counts.HIGH}</div></div>
    `;
  } else {
    // HR / Admin
    const metrics = await api("/admin/metrics").catch(() => null);
    if (metrics) {
      kpiHtml = `
        <div class="kpi-card"><div class="kpi-label">Total Headcount</div><div class="kpi-value">${metrics.total_headcount}</div></div>
        <div class="kpi-card"><div class="kpi-label">Projected Attrition Rate</div><div class="kpi-value" style="color: var(--danger);">${metrics.attrition_summary.projected_attrition_rate_percent}%</div></div>
        <div class="kpi-card"><div class="kpi-label">Vizag Industry Benchmark</div><div class="kpi-value">${metrics.attrition_summary.industry_benchmark_attrition_percent}%</div></div>
        <div class="kpi-card"><div class="kpi-label">Leave Approval Rate</div><div class="kpi-value" style="color: var(--success);">${metrics.leave_trends.approval_rate_percent}%</div></div>
      `;
    }
  }
  kpiRow.innerHTML = kpiHtml;

  // Profile Grid
  const profileGrid = document.getElementById("profile-details-grid");
  profileGrid.innerHTML = `
    <div><strong>Full Name:</strong> ${state.user.full_name}</div>
    <div><strong>Corporate Email:</strong> ${state.user.email}</div>
    <div><strong>System Role:</strong> <span class="badge badge-low">${state.user.role.toUpperCase()}</span></div>
    <div><strong>Department:</strong> ${state.user.department ? state.user.department.name : "Operations"}</div>
    <div><strong>Reporting Manager:</strong> ${state.user.manager ? state.user.manager.full_name : "Executive Leadership"}</div>
    <div><strong>Designation:</strong> ${state.user.job_title || "Staff Member"}</div>
  `;
}

async function loadOnboardingTasks(employeeId) {
  try {
    const data = await api(`/onboarding/${employeeId}`);
    document.getElementById("onboarding-progress-badge").textContent = `${data.completed_tasks}/${data.total_tasks} Completed (${data.completion_rate_percent}%)`;
    
    let html = `<table><thead><tr><th>Task</th><th>Category</th><th>Due Date</th><th>Status</th><th>Action</th></tr></thead><tbody>`;
    data.tasks.forEach(t => {
      html += `
        <tr>
          <td><strong>${t.title}</strong><div style="font-size:0.75rem; color:var(--text-muted);">${t.description || ''}</div></td>
          <td>${t.category}</td>
          <td>${t.due_date || 'N/A'}</td>
          <td><span class="badge ${t.is_completed ? 'badge-approved' : 'badge-pending'}">${t.is_completed ? 'COMPLETED' : 'PENDING'}</span></td>
          <td>
            <button class="secondary" style="font-size:0.75rem; padding:4px 8px;" onclick="toggleTask(${t.id}, ${!t.is_completed})">
              ${t.is_completed ? 'Mark Incomplete' : 'Mark Done'}
            </button>
          </td>
        </tr>
      `;
    });
    html += `</tbody></table>`;
    document.getElementById("onboarding-tasks-list").innerHTML = html;
  } catch (err) {
    document.getElementById("onboarding-tasks-list").innerHTML = `<div style="color: var(--text-muted);">No onboarding tasks assigned.</div>`;
  }
}

async function toggleTask(taskId, isCompleted) {
  await api(`/onboarding/tasks/${taskId}/complete?completed=${isCompleted}`, { method: "PUT" });
  loadOnboardingTasks(state.user.employee_id);
}

// ---------------------------------------------------------------------
// Tab 2: Leave Workflows
// ---------------------------------------------------------------------
async function handleApplyLeave(e) {
  e.preventDefault();
  const feedback = document.getElementById("leave-feedback");
  feedback.textContent = "Submitting...";

  const payload = {
    leave_type: document.getElementById("leave-type").value,
    start_date: document.getElementById("leave-start").value,
    end_date: document.getElementById("leave-end").value,
    reason: document.getElementById("leave-reason").value.trim()
  };

  try {
    await api("/leave/apply", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    feedback.innerHTML = `<span style="color: var(--success);">✓ Leave request submitted successfully.</span>`;
    document.getElementById("leave-form").reset();
    loadLeaveData();
  } catch (err) {
    feedback.innerHTML = `<span style="color: var(--danger);">${err.message}</span>`;
  }
}

async function loadLeaveData() {
  // 1. My leaves
  try {
    const myLeaves = await api("/leave/my");
    let html = `<table><thead><tr><th>Type</th><th>Dates</th><th>Days</th><th>Reason</th><th>Status</th><th>Approver Notes</th></tr></thead><tbody>`;
    if (myLeaves.length === 0) {
      html += `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No leave applications found.</td></tr>`;
    } else {
      myLeaves.forEach(l => {
        const badgeClass = l.status === "APPROVED" ? "badge-approved" : (l.status === "REJECTED" ? "badge-rejected" : "badge-pending");
        html += `
          <tr>
            <td><strong>${l.leave_type}</strong></td>
            <td>${l.start_date} to ${l.end_date}</td>
            <td>${l.days_count}</td>
            <td>${l.reason}</td>
            <td><span class="badge ${badgeClass}">${l.status}</span></td>
            <td>${l.approver_comment || '-'}</td>
          </tr>
        `;
      });
    }
    html += `</tbody></table>`;
    document.getElementById("my-leaves-table-container").innerHTML = html;
  } catch (err) {
    document.getElementById("my-leaves-table-container").innerHTML = `<div style="color:var(--danger);">${err.message}</div>`;
  }

  // 2. Team leaves (if Manager/HR)
  const role = state.user.role.toLowerCase();
  if (["manager", "hr", "admin"].includes(role)) {
    try {
      const teamLeaves = await api("/leave/team");
      let html = `<table><thead><tr><th>Employee</th><th>Leave Type</th><th>Dates</th><th>Days</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead><tbody>`;
      if (teamLeaves.length === 0) {
        html += `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No team leave applications.</td></tr>`;
      } else {
        teamLeaves.forEach(l => {
          const badgeClass = l.status === "APPROVED" ? "badge-approved" : (l.status === "REJECTED" ? "badge-rejected" : "badge-pending");
          const isPending = l.status === "PENDING";
          html += `
            <tr>
              <td><strong>${l.employee_name || 'Team Member'}</strong><div style="font-size:0.75rem; color:var(--text-muted);">${l.employee_code || ''}</div></td>
              <td>${l.leave_type}</td>
              <td>${l.start_date} to ${l.end_date}</td>
              <td>${l.days_count}</td>
              <td>${l.reason}</td>
              <td><span class="badge ${badgeClass}">${l.status}</span></td>
              <td>
                ${isPending ? `
                  <button class="success" style="font-size:0.75rem; padding:4px 8px; margin-right:4px;" onclick="processLeave(${l.id}, 'approve')">Approve</button>
                  <button class="danger" style="font-size:0.75rem; padding:4px 8px;" onclick="processLeave(${l.id}, 'reject')">Reject</button>
                ` : `<span style="font-size:0.8rem; color:var(--text-muted);">${l.approver_comment || 'Decided'}</span>`}
              </td>
            </tr>
          `;
        });
      }
      html += `</tbody></table>`;
      document.getElementById("team-leaves-table-container").innerHTML = html;
    } catch (err) {}
  }
}

async function processLeave(leaveId, action) {
  const comment = prompt(`Enter ${action} comment for employee:`, action === "approve" ? "Approved as per leave balance." : "Rejected due to release schedule.");
  if (comment === null) return;
  await api(`/leave/${leaveId}/${action}`, {
    method: "PUT",
    body: JSON.stringify({ comment })
  });
  loadLeaveData();
}

// ---------------------------------------------------------------------
// Tab 3: Performance Reviews & AI Draft
// ---------------------------------------------------------------------
async function loadReviewsData() {
  const role = state.user.role.toLowerCase();
  
  // Populate employee select dropdown for managers/HR
  if (["manager", "hr", "admin"].includes(role)) {
    const employees = await api("/employees");
    let optionsHtml = `<option value="">-- Choose Employee --</option>`;
    employees.forEach(e => {
      // If manager, highlight direct reports
      optionsHtml += `<option value="${e.id}">${e.full_name} (${e.job_title} • ${e.employee_code})</option>`;
    });
    document.getElementById("review-employee-select").innerHTML = optionsHtml;
  }

  // Load reviews list
  const targetEmpId = state.user.employee_id || 1;
  try {
    const reviews = await api(`/reviews/employee/${targetEmpId}`).catch(() => []);
    let html = `<table><thead><tr><th>Cycle</th><th>Rating</th><th>Overall Summary</th><th>Strengths</th><th>Growth Areas</th><th>Goals</th></tr></thead><tbody>`;
    if (reviews.length === 0) {
      html += `<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">No performance evaluations published.</td></tr>`;
    } else {
      reviews.forEach(r => {
        html += `
          <tr>
            <td><strong>${r.review_cycle}</strong></td>
            <td><span class="badge ${r.rating >= 4 ? 'badge-approved' : (r.rating <= 2 ? 'badge-rejected' : 'badge-pending')}">${r.rating} / 5</span></td>
            <td><div style="font-size:0.85rem; max-width:240px;">${r.feedback || '-'}</div></td>
            <td><div style="font-size:0.85rem; max-width:200px;">${r.strengths || '-'}</div></td>
            <td><div style="font-size:0.85rem; max-width:200px;">${r.growth_areas || '-'}</div></td>
            <td><div style="font-size:0.85rem; max-width:200px;">${r.goals || '-'}</div></td>
          </tr>
        `;
      });
    }
    html += `</tbody></table>`;
    document.getElementById("reviews-history-container").innerHTML = html;
  } catch (err) {
    document.getElementById("reviews-history-container").innerHTML = `<div style="color:var(--text-muted);">Review history unavailable.</div>`;
  }
}

function handleSelectReviewEmployee() {
  state.selectedReviewEmployeeId = document.getElementById("review-employee-select").value;
}

async function handleGenerateAIDraft() {
  const empId = document.getElementById("review-employee-select").value;
  const bulletNotes = document.getElementById("review-bullet-notes").value.trim();
  const statusEl = document.getElementById("ai-draft-status");

  if (!bulletNotes) {
    alert("Please enter manager bullet notes first.");
    return;
  }

  statusEl.textContent = "Generating AI draft with Gemini...";
  try {
    // We pass review_id or dummy 1 for draft generation
    const data = await api(`/reviews/1/ai-draft`, {
      method: "POST",
      body: JSON.stringify({ bullet_notes: bulletNotes })
    });

    document.getElementById("review-narrative").value = data.draft_review;
    document.getElementById("review-strengths").value = data.strengths;
    document.getElementById("review-growth").value = data.growth_areas;
    document.getElementById("review-goals").value = data.goals;
    statusEl.innerHTML = `<span style="color: var(--success);">✓ AI draft generated successfully! Edit before saving.</span>`;
  } catch (err) {
    statusEl.innerHTML = `<span style="color: var(--danger);">${err.message}</span>`;
  }
}

async function handleSaveReview(e) {
  e.preventDefault();
  const empId = document.getElementById("review-employee-select").value;
  if (!empId) {
    alert("Please select an employee.");
    return;
  }

  const payload = {
    employee_id: parseInt(empId),
    review_cycle: document.getElementById("review-cycle-select").value,
    rating: parseInt(document.getElementById("review-rating-select").value),
    feedback: document.getElementById("review-narrative").value.trim(),
    strengths: document.getElementById("review-strengths").value.trim(),
    growth_areas: document.getElementById("review-growth").value.trim(),
    goals: document.getElementById("review-goals").value.trim(),
    status: "COMPLETED"
  };

  try {
    await api("/reviews", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    alert("Performance review successfully published!");
    document.getElementById("review-conduct-form").reset();
    loadReviewsData();
  } catch (err) {
    alert(`Error saving review: ${err.message}`);
  }
}

// ---------------------------------------------------------------------
// Tab 4: GenAI HR Policy Helpdesk (RAG)
// ---------------------------------------------------------------------
async function loadChatHistory() {
  try {
    const history = await api("/chat/history");
    const container = document.getElementById("chat-messages");
    if (history.length > 0) {
      container.innerHTML = "";
      history.reverse().forEach(item => {
        appendChatMessage("user", item.query);
        appendChatMessage("bot", item.answer, item.sources);
      });
    }
  } catch (err) {}
}

function appendChatMessage(sender, text, sources = []) {
  const container = document.getElementById("chat-messages");
  const msgDiv = document.createElement("div");
  msgDiv.className = `chat-message chat-${sender}`;

  let content = `<div>${text.replace(/\n/g, "<br>")}</div>`;
  if (sources && sources.length > 0) {
    content += `<div class="chat-sources"><strong>Verified Sources:</strong> ${sources.map(s => `[${s.title}]`).join(", ")}</div>`;
  }

  msgDiv.innerHTML = content;
  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

async function handleSendChat(e) {
  e.preventDefault();
  const input = document.getElementById("chat-query");
  const query = input.value.trim();
  if (!query) return;

  appendChatMessage("user", query);
  input.value = "";

  const thinkingDiv = document.createElement("div");
  thinkingDiv.className = "chat-message chat-bot";
  thinkingDiv.id = "chat-thinking";
  thinkingDiv.textContent = "Retrieving policy passages and consulting Gemini...";
  document.getElementById("chat-messages").appendChild(thinkingDiv);

  try {
    const data = await api("/chat/ask", {
      method: "POST",
      body: JSON.stringify({ query })
    });
    const tEl = document.getElementById("chat-thinking");
    if (tEl) tEl.remove();
    appendChatMessage("bot", data.answer, data.sources);
  } catch (err) {
    const tEl = document.getElementById("chat-thinking");
    if (tEl) tEl.remove();
    appendChatMessage("bot", `Error: ${err.message}`);
  }
}

// ---------------------------------------------------------------------
// Tab 5: AI Attrition Intelligence (AI 1)
// ---------------------------------------------------------------------
async function loadAttritionData() {
  const container = document.getElementById("attrition-view-container");
  const role = state.user.role.toLowerCase();

  try {
    let html = "";
    if (role === "manager") {
      const data = await api("/attrition/team");
      html += `
        <div style="margin-bottom: 14px;"><strong>Reporting Manager:</strong> ${data.manager_name} | <strong>Team Size:</strong> ${data.team_size}</div>
        <div class="kpi-row" style="margin-bottom: 16px;">
          <div class="kpi-card"><div class="kpi-label">High Risk</div><div class="kpi-value" style="color:var(--danger);">${data.risk_counts.HIGH}</div></div>
          <div class="kpi-card"><div class="kpi-label">Medium Risk</div><div class="kpi-value" style="color:var(--warning);">${data.risk_counts.MEDIUM}</div></div>
          <div class="kpi-card"><div class="kpi-label">Low Risk</div><div class="kpi-value" style="color:var(--success);">${data.risk_counts.LOW}</div></div>
        </div>
        <table><thead><tr><th>Employee</th><th>Designation</th><th>Risk Score</th><th>Risk Band</th><th>Top Contributing Factors</th></tr></thead><tbody>
      `;
      data.employees.forEach(e => {
        const bandClass = e.risk_band === "HIGH" ? "badge-high" : (e.risk_band === "MEDIUM" ? "badge-medium" : "badge-low");
        html += `
          <tr>
            <td><strong>${e.full_name}</strong><div style="font-size:0.75rem; color:var(--text-muted);">${e.employee_code}</div></td>
            <td>${e.job_title}</td>
            <td><strong>${Math.round(e.risk_score * 100)}%</strong></td>
            <td><span class="badge ${bandClass}">${e.risk_band}</span></td>
            <td><ul style="padding-left:16px; font-size:0.8rem;">${e.top_factors.map(f => `<li>${f}</li>`).join('')}</ul></td>
          </tr>
        `;
      });
      html += `</tbody></table>`;
    } else {
      // HR / Admin Dashboard view
      const data = await api("/attrition/dashboard");
      html += `
        <div class="kpi-row" style="margin-bottom: 16px;">
          <div class="kpi-card"><div class="kpi-label">Total Headcount</div><div class="kpi-value">${data.total_headcount}</div></div>
          <div class="kpi-card"><div class="kpi-label">Projected Turnover</div><div class="kpi-value" style="color:var(--danger);">${data.projected_attrition_rate}%</div></div>
          <div class="kpi-card"><div class="kpi-label">High Risk Count</div><div class="kpi-value" style="color:var(--danger);">${data.risk_distribution.HIGH}</div></div>
          <div class="kpi-card"><div class="kpi-label">Medium Risk Count</div><div class="kpi-value" style="color:var(--warning);">${data.risk_distribution.MEDIUM}</div></div>
        </div>

        <h3 style="font-size:1rem; margin:16px 0 8px;">Top High-Risk Employees Requiring Intervention</h3>
        <table><thead><tr><th>Employee</th><th>Department</th><th>Score</th><th>Band</th><th>Top Risk Drivers</th></tr></thead><tbody>
      `;
      data.high_risk_employees.forEach(e => {
        html += `
          <tr>
            <td><strong>${e.full_name}</strong><div style="font-size:0.75rem; color:var(--text-muted);">${e.employee_code} • ${e.job_title}</div></td>
            <td>${e.department_name}</td>
            <td><strong>${Math.round(e.risk_score * 100)}%</strong></td>
            <td><span class="badge badge-high">${e.risk_band}</span></td>
            <td><ul style="padding-left:16px; font-size:0.8rem;">${e.top_factors.map(f => `<li>${f}</li>`).join('')}</ul></td>
          </tr>
        `;
      });
      html += `</tbody></table>`;
    }
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="notice-alert notice-warn">${err.message}</div>`;
  }
}

async function handleRecomputeAttrition() {
  const btn = document.getElementById("btn-recompute-attrition");
  btn.textContent = "Recomputing ML Model...";
  btn.disabled = true;
  try {
    await api("/attrition/recompute", { method: "POST" });
    alert("Batch attrition scores successfully updated across all employees!");
    loadAttritionData();
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    btn.textContent = "⚡ Recompute Batch ML Scores";
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------
// Tab 6: Performance Flags (AI 2)
// ---------------------------------------------------------------------
async function loadPerformanceFlags() {
  const container = document.getElementById("performance-flags-container");
  try {
    const data = await api("/ai/performance-flags");
    let html = `
      <div class="kpi-row" style="margin-bottom: 16px;">
        <div class="kpi-card"><div class="kpi-label">Total Flagged</div><div class="kpi-value">${data.total_flagged}</div></div>
        <div class="kpi-card"><div class="kpi-label">Critical Alerts</div><div class="kpi-value" style="color:var(--danger);">${data.critical_count}</div></div>
        <div class="kpi-card"><div class="kpi-label">Warning Alerts</div><div class="kpi-value" style="color:var(--warning);">${data.warning_count}</div></div>
      </div>
      <table><thead><tr><th>Employee</th><th>Department</th><th>Review History</th><th>Consecutive Drops</th><th>Severity</th><th>Recommended Action</th></tr></thead><tbody>
    `;
    data.flagged_employees.forEach(f => {
      const sevClass = f.severity === "CRITICAL" ? "badge-critical" : "badge-warning";
      const ratingsStr = f.previous_ratings.map(r => `${r.review_cycle}: ${r.rating}★`).join(" → ");
      html += `
        <tr>
          <td><strong>${f.full_name}</strong><div style="font-size:0.75rem; color:var(--text-muted);">${f.employee_code} • ${f.job_title}</div></td>
          <td>${f.department_name}</td>
          <td><div style="font-size:0.8rem; font-weight:600;">${ratingsStr}</div></td>
          <td><strong>${f.consecutive_declines} drops</strong> (Total -${f.total_drop})</td>
          <td><span class="badge ${sevClass}">${f.severity}</span></td>
          <td><div style="font-size:0.8rem; max-width:280px;">${f.action_recommendation}</div></td>
        </tr>
      `;
    });
    html += `</tbody></table>`;
    container.innerHTML = html;
  } catch (err) {
    container.innerHTML = `<div class="notice-alert notice-warn">${err.message}</div>`;
  }
}

// ---------------------------------------------------------------------
// Tab 7: Admin Workforce Metrics
// ---------------------------------------------------------------------
async function loadAdminMetrics() {
  try {
    const data = await api("/admin/metrics");

    // KPI Cards
    document.getElementById("admin-kpi-row").innerHTML = `
      <div class="kpi-card"><div class="kpi-label">Total Staff</div><div class="kpi-value">${data.total_headcount}</div></div>
      <div class="kpi-card"><div class="kpi-label">Total Managers</div><div class="kpi-value">${data.total_managers}</div></div>
      <div class="kpi-card"><div class="kpi-label">Turnover Projection</div><div class="kpi-value" style="color:var(--danger);">${data.attrition_summary.projected_attrition_rate_percent}%</div></div>
      <div class="kpi-card"><div class="kpi-label">Vizag IT Benchmark</div><div class="kpi-value">${data.attrition_summary.industry_benchmark_attrition_percent}%</div></div>
    `;

    // Department Headcount Table
    let deptHtml = `<table><thead><tr><th>Department</th><th>Code</th><th>Headcount</th><th>Share</th></tr></thead><tbody>`;
    data.department_headcounts.forEach(d => {
      deptHtml += `<tr><td><strong>${d.department_name}</strong></td><td>${d.code}</td><td>${d.headcount}</td><td>${d.percentage}%</td></tr>`;
    });
    deptHtml += `</tbody></table>`;
    document.getElementById("dept-metrics-table").innerHTML = deptHtml;

    // Attrition Risk Distribution
    const dist = data.attrition_summary.risk_distribution;
    document.getElementById("risk-metrics-chart").innerHTML = `
      <div style="padding: 10px 0;">
        <div style="margin-bottom: 8px;"><strong>High Risk Band:</strong> ${dist.HIGH} staff (${Math.round((dist.HIGH / data.total_headcount) * 100)}%)</div>
        <div style="margin-bottom: 8px;"><strong>Medium Risk Band:</strong> ${dist.MEDIUM} staff (${Math.round((dist.MEDIUM / data.total_headcount) * 100)}%)</div>
        <div style="margin-bottom: 8px;"><strong>Low Risk Band:</strong> ${dist.LOW} staff (${Math.round((dist.LOW / data.total_headcount) * 100)}%)</div>
        <div style="margin-top: 14px; font-size:0.85rem; color:var(--text-muted);">
          <strong>Critical Departments:</strong> ${data.attrition_summary.critical_departments.join(", ") || "All balanced"}
        </div>
      </div>
    `;

    // Leave Trends
    const lt = data.leave_trends;
    let leaveTypeStr = Object.entries(lt.breakdown_by_type).map(([k, v]) => `<div>${k}: <strong>${v}</strong></div>`).join("");
    document.getElementById("leave-metrics-summary").innerHTML = `
      <div><strong>Total Requests:</strong> ${lt.total_requests}</div>
      <div><strong>Approval Rate:</strong> ${lt.approval_rate_percent}% (${lt.approved_count} Approved, ${lt.pending_count} Pending, ${lt.rejected_count} Rejected)</div>
      <h4 style="margin: 12px 0 6px; font-size:0.85rem;">Volume Breakdown by Type:</h4>
      ${leaveTypeStr}
    `;

    // Review completion
    const rm = data.review_metrics;
    document.getElementById("review-metrics-summary").innerHTML = `
      <div><strong>Total Reviews Conducted:</strong> ${rm.total_reviews_conducted}</div>
      <div><strong>Company Average Rating:</strong> <strong>${rm.average_rating} / 5.0</strong></div>
      <div><strong>Declining Review Alerts:</strong> <span class="badge badge-critical">${rm.flagged_declining_count} Flagged</span></div>
      <div style="margin-top:10px; font-size:0.85rem;">
        Distribution: 5★: ${rm.rating_distribution["5"]} | 4★: ${rm.rating_distribution["4"]} | 3★: ${rm.rating_distribution["3"]} | 2★: ${rm.rating_distribution["2"]} | 1★: ${rm.rating_distribution["1"]}
      </div>
    `;
  } catch (err) {
    document.getElementById("admin-kpi-row").innerHTML = `<div class="notice-alert notice-warn">${err.message}</div>`;
  }
}

// ---------------------------------------------------------------------
// Tab 8: Org & Policy Documents
// ---------------------------------------------------------------------
async function loadOrgData() {
  // Policies List
  try {
    const policies = await api("/policies");
    let html = `<table><thead><tr><th>Title</th><th>Category</th><th>Word Chunks</th><th>Uploaded At</th></tr></thead><tbody>`;
    policies.forEach(p => {
      html += `<tr><td><strong>${p.title}</strong></td><td>${p.category}</td><td>${p.chunk_count} chunks</td><td>${p.created_at.substring(0, 10)}</td></tr>`;
    });
    html += `</tbody></table>`;
    document.getElementById("policies-list-container").innerHTML = html;
  } catch (err) {}

  // Hierarchy Tree
  try {
    const hier = await api("/org/hierarchy");
    let html = `<div style="font-family: monospace; font-size: 0.85rem; line-height: 1.8; background:#fafafa; padding:16px; border-radius:4px;">`;
    
    function renderTree(node, depth = 0) {
      const indent = "&nbsp;&nbsp;".repeat(depth * 3);
      const branch = depth > 0 ? "├── " : "🏢 ";
      let res = `<div>${indent}${branch}<strong>${node.full_name}</strong> (${node.job_title} • ${node.department})</div>`;
      if (node.direct_reports && node.direct_reports.length > 0) {
        node.direct_reports.forEach(child => {
          res += renderTree(child, depth + 1);
        });
      }
      return res;
    }

    hier.hierarchy_trees.forEach(tree => {
      html += renderTree(tree, 0);
    });
    html += `</div>`;
    document.getElementById("hierarchy-tree-container").innerHTML = html;
  } catch (err) {}
}

async function handlePolicyUpload(e) {
  e.preventDefault();
  const feedback = document.getElementById("policy-feedback");
  feedback.textContent = "Uploading and chunking document...";

  const title = document.getElementById("policy-title").value.trim();
  const category = document.getElementById("policy-category").value.trim();
  const fileInput = document.getElementById("policy-file");
  const rawText = document.getElementById("policy-raw-text").value.trim();

  const formData = new FormData();
  formData.append("title", title);
  formData.append("category", category);
  if (fileInput.files.length > 0) {
    formData.append("file", fileInput.files[0]);
  }
  if (rawText) {
    formData.append("raw_text", rawText);
  }

  try {
    await api("/policies/upload", {
      method: "POST",
      body: formData
    });
    feedback.innerHTML = `<span style="color: var(--success);">✓ Policy successfully uploaded and indexed for RAG helpdesk.</span>`;
    document.getElementById("policy-upload-form").reset();
    loadOrgData();
  } catch (err) {
    feedback.innerHTML = `<span style="color: var(--danger);">${err.message}</span>`;
  }
}

// ---------------------------------------------------------------------
// Auto-Run on Load
// ---------------------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  initApp();
});
