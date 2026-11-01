let deptChart = null;
let distChart = null;
let scatterChart = null;

// Map roles to primary screen sections
const ROLE_SECTION_MAP = {
  admin: 'admin-console',
  hr: 'predict-suite',
  employee: 'employee-portal'
};

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/user-status');
    const data = await res.json();

    if (!data.authenticated) {
      window.location.href = '/login.html';
      return;
    }

    const user = data.user;
    const greetingEl = document.getElementById('user-greeting');
    const badgeEl = document.getElementById('role-badge');
    
    if (greetingEl) {
      greetingEl.innerHTML = `<span style="background:rgba(168,85,247,0.2);color:#c084fc;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:700;margin-right:6px;">${user.role.toUpperCase()}</span> ${user.full_name}`;
    }
    if (badgeEl) badgeEl.textContent = user.role.toUpperCase();

    // Professional Role-Based Switcher Filtering (Admin sees all, HR sees HR/Emp, Employee sees none)
    const roleSwitcherGroup = document.querySelector('.role-switcher-group');
    const btnAdmin = document.querySelector('.role-btn-admin');
    const btnHr = document.querySelector('.role-btn-hr');
    const btnEmployee = document.querySelector('.role-btn-employee');

    document.querySelectorAll('.role-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`.role-btn-${user.role}`);
    if (activeBtn) activeBtn.classList.add('active');

    if (user.role === 'admin') {
      if (roleSwitcherGroup) roleSwitcherGroup.style.display = 'inline-flex';
      if (btnAdmin) btnAdmin.style.display = 'inline-block';
      if (btnHr) btnHr.style.display = 'inline-block';
      if (btnEmployee) btnEmployee.style.display = 'inline-block';
    } else if (user.role === 'hr') {
      if (roleSwitcherGroup) roleSwitcherGroup.style.display = 'inline-flex';
      if (btnAdmin) btnAdmin.style.display = 'none'; // HR cannot see or switch to Admin
      if (btnHr) btnHr.style.display = 'inline-block';
      if (btnEmployee) btnEmployee.style.display = 'inline-block';
    } else if (user.role === 'employee') {
      if (roleSwitcherGroup) roleSwitcherGroup.style.display = 'none'; // Completely hidden for employee
    }

    // Load Company Requirements for all users
    loadCompanyRequirements();

    // Configure role-based visibility
    if (user.role === 'employee') {
      document.querySelectorAll('#predict-suite, #exec-metrics, #invite-management, #nav-diag, #visual-analytics, #nav-analytics, #hr-employee-data, #nav-emp-data, #hr-feedback-section, #nav-feedback')
        .forEach(el => el.style.display = 'none');
      
      const empPortal = document.getElementById('employee-portal');
      if (empPortal) empPortal.style.display = 'block';

      const heroTitle = document.querySelector('.hero-title');
      if (heroTitle) heroTitle.innerHTML = `Welcome, <span class="gradient-text">${user.full_name}</span>.`;
      
      const heroSub = document.querySelector('.hero-subtitle');
      if (heroSub) heroSub.textContent = `Department: ${user.department} | Review company expectations or submit confidential well-being feedback.`;
    } else {
      // HR Manager and Admin
      initVisualCharts();
      loadEmployeeDirectory();
      loadFeedbackStream();
    }

    if (user.role === 'admin') {
      const adminNav = document.getElementById('nav-admin');
      const adminSection = document.getElementById('admin-console');
      if (adminNav) adminNav.style.display = 'inline-block';
      if (adminSection) adminSection.style.display = 'block';
      loadAdminUsers();
    }

    // Check for post-switch smooth scroll
    const pendingSectionId = sessionStorage.getItem('scroll_after_login');
    if (pendingSectionId) {
      sessionStorage.removeItem('scroll_after_login');
      setTimeout(() => {
        const targetEl = document.getElementById(pendingSectionId);
        if (targetEl && targetEl.style.display !== 'none') {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 250);
    }

  } catch (err) {
    window.location.href = '/login.html';
    return;
  }

  // Initialize all listeners
  setupAttritionPredictor();
  setupEmployeeFeedback();
  setupInviteForm();
  setupProfilePasswordChange();
  setupAddEmployeeForm();
  setupBulkImportForm();
});

// Role Switcher & Direct Scroll Navigation
async function scrollToRoleSection(targetRole) {
  // Fetch current user status to verify permissions
  try {
    const statusRes = await fetch('/api/user-status');
    const statusData = await statusRes.json();
    const currentRole = statusData.user ? statusData.user.role : null;

    if (currentRole === 'employee' && targetRole !== 'employee') {
      alert('Access Denied: You do not have permission to access the ' + targetRole.toUpperCase() + ' portal.');
      return;
    }
    if (currentRole === 'hr' && targetRole === 'admin') {
      alert('Access Denied: Administrator privileges required.');
      return;
    }
  } catch (e) {}

  const targetId = ROLE_SECTION_MAP[targetRole];
  let element = document.getElementById(targetId);

  if (targetRole === 'employee' && (!element || element.style.display === 'none')) {
    element = document.getElementById('company-reqs');
  }

  // If already accessible and visible on screen, scroll directly
  if (element && element.style.display !== 'none') {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return;
  }

  // Switch role session automatically
  const credentials = {
    admin: { username: 'admin', password: 'admin123' },
    hr: { username: 'hr_manager', password: 'hr123' },
    employee: { username: 'employee_john', password: 'emp123' }
  };

  const cred = credentials[targetRole];
  if (!cred) return;

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cred)
    });
    const data = await res.json();

    if (data.success) {
      sessionStorage.setItem('scroll_after_login', targetId);
      window.location.reload();
    } else {
      alert(`Could not switch to ${targetRole}: ${data.message || 'Login failed'}`);
    }
  } catch (err) {
    alert(`Network error switching to ${targetRole}.`);
  }
}

// Company Requirements
async function loadCompanyRequirements() {
  const grid = document.getElementById('requirements-grid');
  if (!grid) return;

  try {
    const res = await fetch('/api/company-requirements');
    const data = await res.json();
    if (!data.success) return;

    grid.innerHTML = '';
    data.requirements.forEach(req => {
      const card = document.createElement('div');
      card.className = 'req-card';
      const badgeClass = req.mandatory_level === 'Mandatory' ? 'badge-high' : 'badge-low';
      card.innerHTML = `
        <div class="req-header" style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:0.75rem; text-transform:uppercase; color:#a855f7; font-weight:700;">${escapeHtml(req.category)}</span>
          <span class="${badgeClass}" style="font-size:0.75rem; padding: 2px 8px; border-radius:999px;">${escapeHtml(req.mandatory_level)}</span>
        </div>
        <h4 style="margin: 8px 0 6px; font-size: 1.05rem; color: #fff;">${escapeHtml(req.title)}</h4>
        <p style="font-size: 0.86rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 12px;">${escapeHtml(req.description)}</p>
        <div style="font-size: 0.8rem; font-weight: 600; color: #c084fc;">
          Target Benchmark: <span style="color: #fff;">${escapeHtml(req.target_metric || 'Standard')}</span>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    grid.innerHTML = '<p style="color:#fb7185;">Failed to load company standards.</p>';
  }
}

// Workforce Data Directory
async function loadEmployeeDirectory() {
  const tbody = document.getElementById('employee-directory-table-body');
  if (!tbody) return;

  try {
    const res = await fetch('/api/employees/directory');
    const data = await res.json();
    if (!data.success) return;

    if (data.employees.length === 0) {
      tbody.innerHTML = '<tr><td colspan="10" style="padding: 16px; text-align: center; color: var(--text-muted);">No employee records found.</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    data.employees.forEach(emp => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid var(--border-subtle)';
      const riskClass = emp.risk_level === 'High' ? 'badge-high' : (emp.risk_level === 'Moderate' ? 'badge-medium' : 'badge-low');
      const probColor = emp.risk_level === 'High' ? 'text-danger' : (emp.risk_level === 'Moderate' ? 'text-warning' : 'text-success');

      tr.innerHTML = `
        <td style="padding: 12px 14px; font-weight: 600; color: #fff;">${escapeHtml(emp.name)}</td>
        <td style="padding: 12px 14px;">${escapeHtml(emp.department)}</td>
        <td style="padding: 12px 14px;">${emp.satisfaction} / 5</td>
        <td style="padding: 12px 14px;">${emp.tenure} yrs</td>
        <td style="padding: 12px 14px;">${emp.avg_hours} hrs</td>
        <td style="padding: 12px 14px;">${emp.last_evaluation} / 5</td>
        <td style="padding: 12px 14px;">${escapeHtml(emp.salary_level)}</td>
        <td style="padding: 12px 14px;">${escapeHtml(emp.overtime)}</td>
        <td style="padding: 12px 14px; font-weight: 700;" class="${probColor}">${emp.risk_percentage}%</td>
        <td style="padding: 12px 14px;"><span class="${riskClass}" style="padding: 3px 8px; font-size: 0.75rem; border-radius: 999px;">${emp.risk_level}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="10" style="padding:14px; text-align:center; color:#fb7185;">Failed to load employee records.</td></tr>';
  }
}

// Sentiment & Feedback Stream
async function loadFeedbackStream() {
  const tbody = document.getElementById('hr-feedback-table-body');
  if (!tbody) return;

  try {
    const res = await fetch('/api/feedback-list');
    const data = await res.json();
    if (!data.success) return;

    if (data.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="padding: 16px; text-align: center; color: var(--text-muted);">No feedback recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    data.data.forEach(item => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid var(--border-subtle)';
      tr.innerHTML = `
        <td style="padding: 12px 14px; font-size: 0.8rem; color: var(--text-muted);">${item.timestamp.slice(0, 10)}</td>
        <td style="padding: 12px 14px; font-weight: 600; color: #fff;">${escapeHtml(item.full_name)}</td>
        <td style="padding: 12px 14px;">${escapeHtml(item.department)}</td>
        <td style="padding: 12px 14px;"><span class="badge-low" style="padding: 2px 6px; font-size: 0.75rem;">${item.work_life_rating} / 5</span></td>
        <td style="padding: 12px 14px; font-size: 0.82rem;">${escapeHtml(item.workload_pacing)}</td>
        <td style="padding: 12px 14px; color: var(--text-muted); font-size: 0.84rem;">${escapeHtml(item.notes || 'No extra notes provided.')}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="6" style="padding:14px; text-align:center; color:#fb7185;">Failed to load feedback feed.</td></tr>';
  }
}

// Visual Analytics (Chart.js)
async function initVisualCharts() {
  try {
    const res = await fetch('/api/analytics/charts');
    const data = await res.json();
    if (!data.success) return;

    const ctxDept = document.getElementById('chart-dept-risk');
    if (ctxDept) {
      const labels = data.department_risks.map(d => d.department);
      const risks = data.department_risks.map(d => d.avg_risk);

      if (deptChart) deptChart.destroy();
      deptChart = new Chart(ctxDept, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Avg Flight Risk (%)',
            data: risks,
            backgroundColor: 'rgba(168, 85, 247, 0.65)',
            borderColor: '#a855f7',
            borderWidth: 1.5,
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255, 255, 255, 0.06)' }, ticks: { color: '#94a3b8' } },
            x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
          }
        }
      });
    }

    const ctxDist = document.getElementById('chart-risk-dist');
    if (ctxDist) {
      const distLabels = data.risk_distribution.map(d => d.risk_level + ' Risk');
      const distCounts = data.risk_distribution.map(d => d.count);

      if (distChart) distChart.destroy();
      distChart = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
          labels: distLabels,
          datasets: [{
            data: distCounts,
            backgroundColor: ['rgba(244, 63, 94, 0.75)', 'rgba(245, 158, 11, 0.75)', 'rgba(16, 185, 129, 0.75)'],
            borderColor: '#08090d',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom', labels: { color: '#e2e8f0', font: { size: 12 } } } }
        }
      });
    }

    const ctxScatter = document.getElementById('chart-scatter-burnout');
    if (ctxScatter) {
      const points = data.scatter_metrics.map(d => ({
        x: d.avg_hours,
        y: d.satisfaction,
        name: d.name,
        risk: d.risk_percentage
      }));

      if (scatterChart) scatterChart.destroy();
      scatterChart = new Chart(ctxScatter, {
        type: 'scatter',
        data: {
          datasets: [{
            label: 'Evaluated Employees',
            data: points,
            backgroundColor: points.map(p => p.risk > 60 ? 'rgba(244, 63, 94, 0.8)' : 'rgba(56, 189, 248, 0.8)'),
            pointRadius: 7,
            pointHoverRadius: 10
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `${ctx.raw.name}: ${ctx.raw.x} hrs/mo, Satisfaction: ${ctx.raw.y}/5 (${ctx.raw.risk}% Risk)`
              }
            }
          },
          scales: {
            x: { title: { display: true, text: 'Avg Monthly Working Hours', color: '#94a3b8' }, grid: { color: 'rgba(255, 255, 255, 0.06)' }, ticks: { color: '#94a3b8' } },
            y: { title: { display: true, text: 'Job Satisfaction (1 - 5)', color: '#94a3b8' }, min: 1, max: 5, grid: { color: 'rgba(255, 255, 255, 0.06)' }, ticks: { color: '#94a3b8' } }
          }
        }
      });
    }
  } catch (err) {
    console.error('Failed to load visual telemetry charts', err);
  }
}

// Markdown formatter
function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/^# (.*$)/gim, '<h2 style="color:#c084fc;margin-top:14px;margin-bottom:8px;">$1</h2>')
    .replace(/^## (.*$)/gim, '<h3 style="color:#e2e8f0;margin-top:12px;margin-bottom:6px;">$1</h3>')
    .replace(/^### (.*$)/gim, '<h4 style="color:#94a3b8;margin-top:10px;margin-bottom:4px;">$1</h4>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong style="color:#fff;">$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li style="margin-left:18px;">$1</li>')
    .replace(/^\d+\. (.*$)/gim, '<li style="margin-left:18px;list-style-type:decimal;">$1</li>')
    .replace(/\n/gim, '<br/>');
}

// Form Handlers
function setupAttritionPredictor() {
  const form = document.getElementById('attrition-form');
  if (!form) return;

  const btn = document.getElementById('btn-submit');
  const output = document.getElementById('retention-plan-content');
  const probEl = document.getElementById('display-prob');
  const tierEl = document.getElementById('display-tier');
  const driverEl = document.getElementById('display-driver');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
      name: document.getElementById('emp-name').value,
      department: document.getElementById('emp-dept').value,
      satisfaction: document.getElementById('emp-satisfaction').value,
      tenure: document.getElementById('emp-tenure').value,
      avg_hours: document.getElementById('emp-hours').value,
      last_evaluation: document.getElementById('emp-eval').value,
      salary_level: document.getElementById('emp-salary').value,
      overtime: document.getElementById('emp-overtime').value
    };

    btn.disabled = true;
    btn.innerHTML = '<span>⚡ Running Predictive AI & Synthesizing Plan...</span>';
    output.innerHTML = '<div class="empty-state"><p>Evaluating flight risk and compiling retention strategies...</p></div>';

    try {
      const res = await fetch('/api/predict-attrition', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      probEl.textContent = data.risk_percentage + '%';
      tierEl.textContent = data.risk_level.toUpperCase() + ' RISK';
      
      tierEl.className = 'risk-badge';
      if (data.risk_level === 'High') {
        tierEl.classList.add('badge-high');
        probEl.className = 'risk-value text-danger';
      } else if (data.risk_level === 'Moderate') {
        tierEl.classList.add('badge-medium');
        probEl.className = 'risk-value text-warning';
      } else {
        tierEl.classList.add('badge-low');
        probEl.className = 'risk-value text-success';
      }

      driverEl.textContent = data.primary_factors.join(', ');
      output.innerHTML = formatMarkdown(data.retention_plan);

      initVisualCharts();
      loadEmployeeDirectory();

    } catch (err) {
      alert('Error running prediction.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span>⚡ Compute Flight Risk & Generate Retention Plan</span>';
    }
  });
}

function setupEmployeeFeedback() {
  const form = document.getElementById('employee-feedback-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-submit-fb');
    const successBox = document.getElementById('feedback-success');

    btn.disabled = true;
    btn.innerHTML = '<span>Saving...</span>';

    try {
      const res = await fetch('/api/submit-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: document.getElementById('fb-rating').value,
          pacing: document.getElementById('fb-pacing').value,
          notes: document.getElementById('fb-notes').value
        })
      });
      const data = await res.json();

      if (data.success) {
        successBox.style.display = 'block';
        form.reset();
        setTimeout(() => { successBox.style.display = 'none'; }, 4000);
      } else {
        alert(data.error || 'Submission failed');
      }
    } catch (err) {
      alert('Network error submitting feedback.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span>Submit Confidential Feedback</span>';
    }
  });
}

function setupInviteForm() {
  const form = document.getElementById('invite-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      email: document.getElementById('inv-email').value,
      department: document.getElementById('inv-dept').value,
      role: document.getElementById('inv-role').value
    };

    try {
      const res = await fetch('/api/create-invite', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('invite-result-box').style.display = 'block';
        document.getElementById('invite-link-output').value = data.invite_url;
      }
    } catch (err) {
      alert('Failed to generate invite link.');
    }
  });
}

// Modal Handlers
function openPasswordModal() {
  document.getElementById('password-modal').style.display = 'flex';
}

function closePasswordModal() {
  document.getElementById('password-modal').style.display = 'none';
  document.getElementById('profile-password-form').reset();
}

function setupProfilePasswordChange() {
  const form = document.getElementById('profile-password-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-save-pw');
    btn.disabled = true;

    try {
      const res = await fetch('/api/profile/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: document.getElementById('pw-current').value,
          new_password: document.getElementById('pw-new').value
        })
      });
      const data = await res.json();

      if (data.success) {
        alert(data.message);
        closePasswordModal();
      } else {
        alert(data.error || 'Failed to change password.');
      }
    } catch (err) {
      alert('Network error while updating password.');
    } finally {
      btn.disabled = false;
    }
  });
}

function openAddEmployeeModal() {
  document.getElementById('add-employee-modal').style.display = 'flex';
}

function closeAddEmployeeModal() {
  document.getElementById('add-employee-modal').style.display = 'none';
  document.getElementById('add-employee-form').reset();
}

function setupAddEmployeeForm() {
  const form = document.getElementById('add-employee-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-save-employee');
    btn.disabled = true;
    btn.innerHTML = '<span>Saving Record...</span>';

    const payload = {
      name: document.getElementById('add-emp-name').value,
      department: document.getElementById('add-emp-dept').value,
      satisfaction: document.getElementById('add-emp-satisfaction').value,
      tenure: document.getElementById('add-emp-tenure').value,
      avg_hours: document.getElementById('add-emp-hours').value,
      last_evaluation: document.getElementById('add-emp-eval').value,
      salary_level: document.getElementById('add-emp-salary').value,
      overtime: document.getElementById('add-emp-overtime').value
    };

    try {
      const res = await fetch('/api/employees/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        alert(data.message);
        closeAddEmployeeModal();
        loadEmployeeDirectory();
        if (typeof initVisualCharts === 'function') initVisualCharts();
      } else {
        alert(data.error || 'Failed to add employee.');
      }
    } catch (err) {
      alert('Network error while saving employee.');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span>Save & Add to Directory</span>';
    }
  });
}

function openBulkUploadModal() {
  document.getElementById('bulk-upload-modal').style.display = 'flex';
}

function closeBulkUploadModal() {
  document.getElementById('bulk-upload-modal').style.display = 'none';
  document.getElementById('bulk-import-form').reset();
}

function downloadCsvTemplate() {
  const headers = "name,department,satisfaction,tenure,avg_hours,last_evaluation,salary_level,overtime\n";
  const sampleData = [
    "Jordan Lee,Engineering,2.3,3.0,225,4.2,Medium,Yes",
    "Marcus Vance,Sales,3.8,2.5,185,3.9,High,No",
    "Aria Montgomery,Product,1.8,4.5,240,4.6,Low,Yes",
    "Nathan Cole,Operations,4.1,1.5,170,3.7,Medium,No"
  ].join("\n");

  const blob = new Blob([headers + sampleData], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const downloadLink = document.createElement("a");
  downloadLink.setAttribute("href", url);
  downloadLink.setAttribute("download", "talentpulse_employee_template.csv");
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
}

function setupBulkImportForm() {
  const form = document.getElementById('bulk-import-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('csv-file-input');
    const btn = document.getElementById('btn-upload-csv');

    if (!fileInput.files.length) {
      alert("Please select a CSV file first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    btn.disabled = true;
    btn.innerHTML = '<span>Processing Records...</span>';

    try {
      const res = await fetch('/api/employees/bulk-import', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (data.success) {
        alert(data.message);
        closeBulkUploadModal();
        loadEmployeeDirectory();
        if (typeof initVisualCharts === 'function') initVisualCharts();
      } else {
        alert(data.error || "Import failed.");
      }
    } catch (err) {
      alert("Network error occurred during CSV upload.");
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<span>Upload & Process CSV</span>';
    }
  });
}

// Admin Panel Logic
async function loadAdminUsers() {
  const tbody = document.getElementById('admin-user-table-body');
  if (!tbody) return;

  try {
    const res = await fetch('/api/admin/users');
    const data = await res.json();
    if (!data.success) return;

    tbody.innerHTML = '';
    data.users.forEach(u => {
      const tr = document.createElement('tr');
      tr.style.borderBottom = '1px solid var(--border-subtle)';
      tr.innerHTML = `
        <td style="padding: 12px 14px; font-weight: 600;">${escapeHtml(u.full_name)}</td>
        <td style="padding: 12px 14px; color: var(--text-muted);">${escapeHtml(u.username)}</td>
        <td style="padding: 12px 14px;">${escapeHtml(u.department)}</td>
        <td style="padding: 12px 14px;">
          <select onchange="updateUserRole(${u.id}, this.value)" style="padding: 4px 8px; font-size: 0.8rem; width: auto;">
            <option value="employee" ${u.role === 'employee' ? 'selected' : ''}>Employee</option>
            <option value="hr" ${u.role === 'hr' ? 'selected' : ''}>HR Manager</option>
            <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>Administrator</option>
          </select>
        </td>
        <td style="padding: 12px 14px; text-align: right; display: flex; gap: 8px; justify-content: flex-end;">
          <button onclick="adminResetPassword(${u.id}, '${escapeHtml(u.username)}')" class="btn-copy" style="color: #38bdf8; border-color: rgba(56, 189, 248, 0.3);">Reset PW</button>
          <button onclick="deleteUser(${u.id})" class="btn-copy" style="color: #fb7185; border-color: rgba(244, 63, 94, 0.3);">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="5" style="padding: 14px; text-align: center; color: #fb7185;">Failed to load accounts.</td></tr>';
  }
}

async function updateUserRole(userId, newRole) {
  try {
    const res = await fetch(`/api/admin/users/${userId}/role`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole })
    });
    const result = await res.json();
    if (!result.success) alert(result.error);
  } catch (err) {
    alert('Error updating user role.');
  }
}

async function adminResetPassword(userId, username) {
  const newPassword = prompt(`Enter a new temporary password for ${username} (min 6 characters):`);
  if (!newPassword || newPassword.trim().length < 6) return;

  try {
    const res = await fetch(`/api/admin/users/${userId}/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_password: newPassword.trim() })
    });
    const result = await res.json();
    if (result.success) {
      alert(`Password for ${username} reset successfully to: ${newPassword.trim()}`);
    } else {
      alert(result.error || "Failed to reset password.");
    }
  } catch (err) {
    alert("Network error while resetting password.");
  }
}

async function deleteUser(userId) {
  if (!confirm('Permanently delete this user account?')) return;
  try {
    const res = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.success) loadAdminUsers();
  } catch (err) {
    alert('Failed to delete account.');
  }
}

function copyRetentionPlan() {
  const content = document.getElementById('retention-plan-content').innerText;
  navigator.clipboard.writeText(content).then(() => alert('Retention plan copied to clipboard!'));
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
