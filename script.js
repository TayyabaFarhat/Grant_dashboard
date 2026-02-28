/* =============================================
   LAUNCHPAD INTELLIGENCE — Dashboard Script
   ============================================= */

'use strict';

// State
const state = {
  opportunities: [],
  filtered: [],
  activeTab: 'all',
  search: '',
  filterCategory: '',
  filterCountry: '',
  filterStatus: '',
  filterSort: 'date_added',
  statFilter: null,
};

// DOM refs
const $ = id => document.getElementById(id);
const grid = $('opportunitiesGrid');
const loadingState = $('loadingState');
const emptyState = $('emptyState');

// ---- INIT ----
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  initEventListeners();
  await loadData();
});

// ---- THEME ----
function initTheme() {
  const saved = localStorage.getItem('lp-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
}

$('themeToggle').addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('lp-theme', next);
});

// ---- LOAD DATA ----
async function loadData() {
  try {
    const res = await fetch('opportunities.json?v=' + Date.now());
    const data = await res.json();
    state.opportunities = computeStatus(data.opportunities);
    populateCountryFilter();
    updateHeroMeta(data);
    applyFiltersAndRender();
  } catch (err) {
    console.error('Failed to load data:', err);
    loadingState.innerHTML = `<p style="color:var(--red)">⚠ Failed to load opportunities. Please refresh.</p>`;
  }
}

// ---- COMPUTE STATUS ----
function computeStatus(opportunities) {
  const now = new Date();
  const twoDaysAgo = new Date(now - 2 * 24 * 60 * 60 * 1000);
  const sevenDays = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  return opportunities.map(opp => {
    const deadline = opp.deadline ? new Date(opp.deadline) : null;
    const dateAdded = opp.date_added ? new Date(opp.date_added) : null;

    let status = opp.status || 'open';

    if (deadline) {
      if (deadline < now) {
        status = 'closed';
      } else if (deadline <= sevenDays) {
        status = 'closing_soon';
      }
    }

    if (dateAdded && dateAdded >= twoDaysAgo && status === 'open') {
      status = 'new';
    }

    return { ...opp, status };
  });
}

// ---- POPULATE COUNTRY FILTER ----
function populateCountryFilter() {
  const countries = [...new Set(state.opportunities.map(o => o.country).filter(Boolean))].sort();
  const sel = $('filterCountry');
  countries.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    sel.appendChild(opt);
  });
}

// ---- HERO META ----
function updateHeroMeta(data) {
  $('metaTotal').textContent = `${data.total} opportunities`;
  if (data.last_updated) {
    const d = new Date(data.last_updated);
    $('metaUpdated').textContent = `Updated ${formatRelative(d)}`;
    $('footerUpdated').textContent = `Last updated: ${d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;
  }
}

// ---- APPLY FILTERS ----
function applyFiltersAndRender() {
  let data = [...state.opportunities];

  // Tab filter
  if (state.activeTab !== 'all') {
    data = data.filter(o => o.type === state.activeTab);
  }

  // Stat card filter
  if (state.statFilter === 'closing') {
    data = data.filter(o => o.status === 'closing_soon');
  } else if (state.statFilter && state.statFilter !== 'all') {
    data = data.filter(o => o.type === state.statFilter);
  }

  // Search
  if (state.search) {
    const q = state.search.toLowerCase();
    data = data.filter(o =>
      (o.name || '').toLowerCase().includes(q) ||
      (o.organization || '').toLowerCase().includes(q) ||
      (o.country || '').toLowerCase().includes(q) ||
      (o.description || '').toLowerCase().includes(q) ||
      (o.tags || []).some(t => t.toLowerCase().includes(q))
    );
  }

  // Category filter
  if (state.filterCategory) {
    data = data.filter(o => o.type === state.filterCategory);
  }

  // Country filter
  if (state.filterCountry) {
    data = data.filter(o => o.country === state.filterCountry);
  }

  // Status filter
  if (state.filterStatus) {
    data = data.filter(o => o.status === state.filterStatus);
  }

  // Sort
  data.sort((a, b) => {
    if (state.filterSort === 'deadline') {
      const da = a.deadline ? new Date(a.deadline) : new Date('9999');
      const db = b.deadline ? new Date(b.deadline) : new Date('9999');
      return da - db;
    }
    if (state.filterSort === 'prize') {
      return extractNumber(b.prize) - extractNumber(a.prize);
    }
    // date_added default
    const da = a.date_added ? new Date(a.date_added) : new Date(0);
    const db = b.date_added ? new Date(b.date_added) : new Date(0);
    return db - da;
  });

  state.filtered = data;
  updateStats();
  renderGrid();
}

function extractNumber(str) {
  if (!str) return 0;
  const match = str.replace(/,/g, '').match(/[\d.]+/);
  return match ? parseFloat(match[0]) : 0;
}

// ---- UPDATE STATS ----
function updateStats() {
  const all = state.opportunities;
  $('statTotal').textContent = all.length;
  $('statGrants').textContent = all.filter(o => o.type === 'grant').length;
  $('statComps').textContent = all.filter(o => o.type === 'competition').length;
  $('statAccel').textContent = all.filter(o => o.type === 'accelerator').length;
  $('statClosing').textContent = all.filter(o => o.status === 'closing_soon').length;
  $('resultsCount').textContent = `${state.filtered.length} result${state.filtered.length !== 1 ? 's' : ''}`;
}

// ---- RENDER GRID ----
function renderGrid() {
  loadingState.classList.add('hidden');

  if (state.filtered.length === 0) {
    emptyState.classList.remove('hidden');
    grid.innerHTML = '';
    return;
  }

  emptyState.classList.add('hidden');
  grid.innerHTML = '';

  state.filtered.forEach((opp, i) => {
    const card = createCard(opp, i);
    grid.appendChild(card);
  });
}

// ---- CREATE CARD ----
function createCard(opp, index) {
  const el = document.createElement('article');
  el.className = 'opp-card';
  el.style.animationDelay = `${Math.min(index * 0.04, 0.5)}s`;

  const statusLabel = {
    open: '● Open',
    closing_soon: '⚡ Closing Soon',
    closed: '✕ Closed',
    new: '✦ New',
  }[opp.status] || 'Open';

  const deadline = opp.deadline ? formatDeadline(opp.deadline) : 'Rolling';
  const tags = (opp.tags || []).slice(0, 3);

  el.innerHTML = `
    <div class="card-header">
      <div class="card-org-wrap">
        <span class="card-org">${escHtml(opp.organization || '')}</span>
        <h2 class="card-title">${escHtml(opp.name || 'Untitled Opportunity')}</h2>
      </div>
      <div class="card-badges">
        <span class="status-badge status-${opp.status}">${statusLabel}</span>
        <span class="type-badge type-${opp.type}">${capitalize(opp.type || 'other')}</span>
      </div>
    </div>

    <p class="card-description">${escHtml(opp.description || '')}</p>

    <div class="card-meta">
      <div class="meta-item-card meta-prize">
        <span class="meta-key">Prize / Funding</span>
        <span class="meta-val">${escHtml(opp.prize || 'Varies')}</span>
      </div>
      <div class="meta-item-card meta-deadline">
        <span class="meta-key">Deadline</span>
        <span class="meta-val">${deadline}</span>
      </div>
      <div class="meta-item-card">
        <span class="meta-key">Country</span>
        <span class="meta-val">${escHtml(opp.country || 'Global')}</span>
      </div>
      <div class="meta-item-card">
        <span class="meta-key">Category</span>
        <span class="meta-val">${capitalize(opp.category || opp.type || '')}</span>
      </div>
    </div>

    ${tags.length ? `<div class="card-tags">${tags.map(t => `<span class="tag">#${escHtml(t)}</span>`).join('')}</div>` : ''}

    <div class="card-actions">
      <a href="${escHtml(opp.link || '#')}" target="_blank" rel="noopener noreferrer" class="btn-primary">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        Apply Now
      </a>
      <a href="${escHtml(opp.link || '#')}" target="_blank" rel="noopener noreferrer" class="btn-secondary">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        Visit
      </a>
    </div>
  `;

  return el;
}

// ---- EVENT LISTENERS ----
function initEventListeners() {
  // Tab clicks
  document.querySelectorAll('.tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      state.activeTab = btn.dataset.tab;
      state.statFilter = null;
      clearStatActive();
      applyFiltersAndRender();
    });
  });

  // Stat card clicks
  document.querySelectorAll('.stat-card').forEach(card => {
    card.addEventListener('click', () => {
      const f = card.dataset.filter;
      if (state.statFilter === f) {
        state.statFilter = null;
        card.classList.remove('active');
      } else {
        clearStatActive();
        state.statFilter = f;
        card.classList.add('active');
      }
      applyFiltersAndRender();
    });
  });

  // Search
  $('searchInput').addEventListener('input', e => {
    state.search = e.target.value;
    $('searchClear').classList.toggle('visible', state.search.length > 0);
    applyFiltersAndRender();
  });

  $('searchClear').addEventListener('click', () => {
    $('searchInput').value = '';
    state.search = '';
    $('searchClear').classList.remove('visible');
    applyFiltersAndRender();
  });

  // Filters
  $('filterCategory').addEventListener('change', e => { state.filterCategory = e.target.value; applyFiltersAndRender(); });
  $('filterCountry').addEventListener('change', e => { state.filterCountry = e.target.value; applyFiltersAndRender(); });
  $('filterStatus').addEventListener('change', e => { state.filterStatus = e.target.value; applyFiltersAndRender(); });
  $('filterSort').addEventListener('change', e => { state.filterSort = e.target.value; applyFiltersAndRender(); });

  // Reset buttons
  $('resetFilters').addEventListener('click', resetAll);
  $('resetFromEmpty').addEventListener('click', resetAll);
}

function resetAll() {
  state.search = '';
  state.filterCategory = '';
  state.filterCountry = '';
  state.filterStatus = '';
  state.filterSort = 'date_added';
  state.activeTab = 'all';
  state.statFilter = null;

  $('searchInput').value = '';
  $('filterCategory').value = '';
  $('filterCountry').value = '';
  $('filterStatus').value = '';
  $('filterSort').value = 'date_added';
  $('searchClear').classList.remove('visible');

  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelector('.tab[data-tab="all"]').classList.add('active');
  clearStatActive();

  applyFiltersAndRender();
}

function clearStatActive() {
  document.querySelectorAll('.stat-card').forEach(c => c.classList.remove('active'));
}

// ---- HELPERS ----
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function formatDeadline(dateStr) {
  const d = new Date(dateStr);
  const now = new Date();
  const diff = d - now;
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24));

  if (days < 0) return 'Closed';
  if (days === 0) return 'Today!';
  if (days <= 7) return `${days}d left`;
  if (days <= 30) return `${Math.ceil(days / 7)}w left`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatRelative(date) {
  const diff = Date.now() - date.getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return 'just now';
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
