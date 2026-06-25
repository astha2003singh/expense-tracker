/* ── ExpenseTrack Dashboard JS ────────────────────────────── */

const API = {
  stats:       () => fetch('/api/stats').then(r => r.json()),
  expenses:    (p) => fetch('/api/expenses?' + new URLSearchParams(p)).then(r => r.json()),
  addExpense:  (d) => fetch('/api/expenses', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d) }).then(r => r.json()),
  delExpense:  (id) => fetch(`/api/expenses/${id}`, { method:'DELETE' }).then(r => r.json()),
  categories:  () => fetch('/api/categories').then(r => r.json()),
  catTotals:   (p) => fetch('/api/category-totals?' + new URLSearchParams(p||{})).then(r => r.json()),
  monthTotals: (n) => fetch('/api/monthly-totals?months='+(n||6)).then(r => r.json()),
  dailyTotals: () => fetch('/api/daily-totals').then(r => r.json()),
  budgets:     () => fetch('/api/budgets').then(r => r.json()),
  setBudget:   (d) => fetch('/api/budget', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(d) }).then(r => r.json()),
  uploadPdf:   (fd) => fetch('/api/upload-pdf', { method:'POST', body:fd }).then(r => r.json()),
};

// ── State ──────────────────────────────────────────────────
let charts = {};
let categoriesCache = [];

// ── Helpers ────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);
const fmt = (n) => '₹' + Number(n).toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 0 });

function showToast(msg, type = 'success') {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast show ' + type;
  setTimeout(() => t.className = 'toast', 3000);
}

function setDate() {
  const today = new Date().toISOString().split('T')[0];
  $('#input-date').value = today;
  const ym = today.slice(0, 7);
  $('#filter-month').value = ym;
}

// ── Navigation ─────────────────────────────────────────────
function switchView(name) {
  $$('.view').forEach(v => v.classList.remove('active'));
  $$('.nav-item').forEach(n => n.classList.remove('active'));
  const view = $(`#view-${name}`);
  if (view) view.classList.add('active');
  const nav = $(`[data-view="${name}"]`);
  if (nav) nav.classList.add('active');
  const titles = { dashboard:'Dashboard', expenses:'Expenses', budgets:'Budgets', analytics:'Analytics' };
  $('#topbar-title').textContent = titles[name] || 'Dashboard';
  if (name === 'dashboard') loadDashboard();
  if (name === 'expenses') loadExpenses();
  if (name === 'budgets') loadBudgets();
  if (name === 'analytics') loadAnalytics();
}

// ── Dashboard ──────────────────────────────────────────────
async function loadDashboard() {
  const [stats, catTotals, monthTotals, expenses] = await Promise.all([
    API.stats(), API.catTotals(), API.monthTotals(6), API.expenses({ limit: 5 })
  ]);

  $('#val-month-total').textContent = fmt(stats.total_this_month);
  $('#val-all-time').textContent = fmt(stats.total_all_time);
  $('#val-count').textContent = stats.expense_count;
  $('#val-budget-left').textContent = stats.budget_set ? fmt(stats.budget_remaining) : '—';

  renderRecentTable(expenses);
  renderMonthlyChart(monthTotals);
  renderCategoryChart(catTotals, 'chart-category');
}

function renderRecentTable(expenses) {
  const tb = $('#tbody-recent');
  if (!expenses.length) { tb.innerHTML = '<tr><td colspan="4" class="empty-state">No expenses yet. Add one!</td></tr>'; return; }
  tb.innerHTML = expenses.map(e => {
    const d = new Date(e.date).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
    const cat = categoriesCache.find(c => c.name === e.category);
    const color = cat ? cat.color : '#868e96';
    return `<tr>
      <td>${d}</td>
      <td><span class="cat-badge"><span class="cat-dot" style="background:${color}"></span>${e.category}</span></td>
      <td>${e.note || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td class="text-right" style="font-weight:600">${fmt(e.amount)}</td>
    </tr>`;
  }).join('');
}

function renderMonthlyChart(data) {
  const ctx = $('#chart-monthly-trend');
  if (charts.monthly) charts.monthly.destroy();
  charts.monthly = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.month),
      datasets: [{
        label: 'Spending',
        data: data.map(d => d.total),
        backgroundColor: 'rgba(108,92,231,.45)',
        borderColor: '#6c5ce7',
        borderWidth: 2,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: chartOpts('₹')
  });
}

function renderCategoryChart(data, canvasId) {
  const ctx = $(`#${canvasId}`);
  const key = canvasId;
  if (charts[key]) charts[key].destroy();
  if (!data.length) { charts[key] = null; return; }
  charts[key] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.map(d => d.category),
      datasets: [{
        data: data.map(d => d.total),
        backgroundColor: data.map(d => d.color),
        borderWidth: 0,
        hoverOffset: 8,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: { position:'bottom', labels:{ color:'#8b8fa3', padding:14, font:{ family:'Inter', size:12 }, usePointStyle:true, pointStyleWidth:8 } },
        tooltip: { backgroundColor:'#1a1d27', titleColor:'#e4e6f0', bodyColor:'#e4e6f0', borderColor:'#2e3144', borderWidth:1, padding:10, cornerRadius:8 }
      }
    }
  });
}

function chartOpts(prefix) {
  return {
    responsive:true, maintainAspectRatio:false,
    plugins:{
      legend:{ display:false },
      tooltip:{ backgroundColor:'#1a1d27', titleColor:'#e4e6f0', bodyColor:'#e4e6f0', borderColor:'#2e3144', borderWidth:1, padding:10, cornerRadius:8, callbacks:{ label: ctx => prefix + Number(ctx.raw).toLocaleString('en-IN') } }
    },
    scales:{
      x:{ grid:{ color:'rgba(46,49,68,.5)' }, ticks:{ color:'#5c6078', font:{ family:'Inter', size:11 } } },
      y:{ grid:{ color:'rgba(46,49,68,.5)' }, ticks:{ color:'#5c6078', font:{ family:'Inter', size:11 }, callback: v => prefix + (v>=1000?(v/1000)+'k':v) }, beginAtZero:true }
    }
  };
}

// ── Expenses View ──────────────────────────────────────────
async function loadExpenses() {
  const params = {};
  const cat = $('#filter-category').value;
  const monthVal = $('#filter-month').value;
  if (cat) params.category = cat;
  if (monthVal) { const [y,m] = monthVal.split('-'); params.month = parseInt(m); params.year = parseInt(y); }
  params.limit = 100;
  const expenses = await API.expenses(params);
  const tb = $('#tbody-expenses');
  if (!expenses.length) { tb.innerHTML = '<tr><td colspan="6" class="empty-state">No expenses found.</td></tr>'; return; }
  tb.innerHTML = expenses.map(e => {
    const d = new Date(e.date).toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' });
    const cat = categoriesCache.find(c => c.name === e.category);
    const color = cat ? cat.color : '#868e96';
    return `<tr>
      <td style="color:var(--text-muted)">#${e.id}</td>
      <td>${d}</td>
      <td><span class="cat-badge"><span class="cat-dot" style="background:${color}"></span>${e.category}</span></td>
      <td>${e.note || '<span style="color:var(--text-muted)">—</span>'}</td>
      <td class="text-right" style="font-weight:600">${fmt(e.amount)}</td>
      <td class="text-center"><button class="btn-danger" onclick="deleteExpense(${e.id})">Delete</button></td>
    </tr>`;
  }).join('');
}

async function deleteExpense(id) {
  if (!confirm('Delete expense #' + id + '?')) return;
  await API.delExpense(id);
  showToast('Expense deleted');
  loadExpenses();
  loadDashboard();
}

// ── Budgets View ───────────────────────────────────────────
async function loadBudgets() {
  const budgets = await API.budgets();
  const grid = $('#budgets-grid');
  if (!budgets.length) { grid.innerHTML = '<div class="empty-card"><p>No budgets set.</p><p class="empty-hint">Click "Set Budget" to start.</p></div>'; return; }
  grid.innerHTML = budgets.map(b => {
    const pct = Math.min(b.percentage, 100);
    let barColor = 'var(--green)';
    if (b.percentage >= 100) barColor = 'var(--red)';
    else if (b.percentage >= 80) barColor = 'var(--orange)';
    return `<div class="budget-card">
      <div class="budget-label">${b.category}</div>
      <div class="budget-amount">${fmt(b.amount)}</div>
      <div class="budget-bar"><div class="budget-bar-fill" style="width:${pct}%;background:${barColor}"></div></div>
      <div class="budget-meta"><span>Spent: ${fmt(b.spent)}</span><span>${b.percentage.toFixed(0)}%</span></div>
    </div>`;
  }).join('');
}

// ── Analytics View ─────────────────────────────────────────
async function loadAnalytics() {
  const [daily, monthly, catTotals] = await Promise.all([
    API.dailyTotals(), API.monthTotals(6), API.catTotals()
  ]);

  // Daily chart
  const ctx1 = $('#chart-daily');
  if (charts.daily) charts.daily.destroy();
  charts.daily = new Chart(ctx1, {
    type: 'line',
    data: {
      labels: daily.map(d => d.day.slice(5)),
      datasets: [{
        label: 'Daily',
        data: daily.map(d => d.total),
        borderColor: '#6c5ce7',
        backgroundColor: 'rgba(108,92,231,.1)',
        fill: true,
        tension: .4,
        pointRadius: 3,
        pointBackgroundColor: '#6c5ce7',
      }]
    },
    options: chartOpts('₹')
  });

  // Trend detail
  const ctx2 = $('#chart-trend-detail');
  if (charts.trendDetail) charts.trendDetail.destroy();
  charts.trendDetail = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: monthly.map(d => d.month),
      datasets: [{
        label: 'Spending',
        data: monthly.map(d => d.total),
        backgroundColor: ['#6c5ce7','#a29bfe','#74b9ff','#00cec9','#fdcb6e','#ff6b6b'],
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: chartOpts('₹')
  });

  renderCategoryChart(catTotals, 'chart-category-detail');
}

// ── Modals ─────────────────────────────────────────────────
function openModal(id) { $(`#${id}`).classList.add('open'); }
function closeModal(id) { $(`#${id}`).classList.remove('open'); }

// ── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Load categories
  categoriesCache = await API.categories();
  const catOpts = categoriesCache.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
  $('#input-category').innerHTML = '<option value="">Select...</option>' + catOpts;
  $('#filter-category').innerHTML = '<option value="">All Categories</option>' + catOpts;
  $('#budget-category').innerHTML = '<option value="">Overall Budget</option>' + catOpts;

  setDate();
  loadDashboard();

  // Nav clicks
  $$('.nav-item, .card-link[data-view]').forEach(el => {
    el.addEventListener('click', e => { e.preventDefault(); switchView(el.dataset.view); });
  });

  // Sidebar toggle (mobile)
  $('#menu-toggle').addEventListener('click', () => $('#sidebar').classList.toggle('open'));

  // Add expense modal
  $('#btn-add-expense').addEventListener('click', () => { setDate(); openModal('modal-overlay'); });
  $('#modal-close').addEventListener('click', () => closeModal('modal-overlay'));
  $('#btn-cancel').addEventListener('click', () => closeModal('modal-overlay'));
  $('#modal-overlay').addEventListener('click', e => { if (e.target === $('#modal-overlay')) closeModal('modal-overlay'); });

  // Budget modal
  $('#btn-set-budget').addEventListener('click', () => openModal('modal-overlay-budget'));
  $('#modal-budget-close').addEventListener('click', () => closeModal('modal-overlay-budget'));
  $('#btn-budget-cancel').addEventListener('click', () => closeModal('modal-overlay-budget'));
  $('#modal-overlay-budget').addEventListener('click', e => { if (e.target === $('#modal-overlay-budget')) closeModal('modal-overlay-budget'); });

  // Add expense form
  $('#form-add-expense').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
      amount: parseFloat($('#input-amount').value),
      category: $('#input-category').value,
      note: $('#input-note').value,
      date: $('#input-date').value,
    };
    if (!data.amount || !data.category) { showToast('Please fill required fields', 'error'); return; }
    await API.addExpense(data);
    closeModal('modal-overlay');
    $('#form-add-expense').reset();
    showToast('Expense added!');
    loadDashboard();
  });

  // PDF modal and form
  $('#btn-upload-pdf').addEventListener('click', () => openModal('modal-overlay-pdf'));
  $('#modal-pdf-close').addEventListener('click', () => closeModal('modal-overlay-pdf'));
  $('#btn-pdf-cancel').addEventListener('click', () => closeModal('modal-overlay-pdf'));
  $('#modal-overlay-pdf').addEventListener('click', e => { if (e.target === $('#modal-overlay-pdf')) closeModal('modal-overlay-pdf'); });

  $('#form-upload-pdf').addEventListener('submit', async e => {
    e.preventDefault();
    const file = $('#pdf-file').files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    const btn = $('#form-upload-pdf').querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'Uploading...';
    btn.disabled = true;
    
    try {
        const res = await API.uploadPdf(formData);
        if (res.error) {
            showToast(res.error, 'error');
        } else {
            showToast(`Successfully extracted ${res.count} expenses!`);
            closeModal('modal-overlay-pdf');
            $('#form-upload-pdf').reset();
            loadDashboard();
            if ($('#view-expenses').classList.contains('active')) {
                loadExpenses();
            }
        }
    } catch(err) {
        showToast('Error uploading PDF', 'error');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
  });

  // Set budget form
  $('#form-set-budget').addEventListener('submit', async e => {
    e.preventDefault();
    const data = {
      amount: parseFloat($('#budget-amount').value),
      category: $('#budget-category').value || null,
    };
    if (!data.amount) { showToast('Please enter an amount', 'error'); return; }
    await API.setBudget(data);
    closeModal('modal-overlay-budget');
    $('#form-set-budget').reset();
    showToast('Budget set!');
    loadBudgets();
    loadDashboard();
  });

  // Filters
  $('#filter-category').addEventListener('change', loadExpenses);
  $('#filter-month').addEventListener('change', loadExpenses);
});
