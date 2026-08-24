/* companies.js */

let currentTab     = 'jobs';
let currentPage    = 1;
let currentLayout  = 'grid';
let currentJobId   = null;
let debounceTimer  = null;

document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  loadDomains();
});

// ── Tab switching ─────────────────────────────────────────────────────────────
function switchTab(tab, btn) {
  currentTab  = tab;
  currentPage = 1;
  document.querySelectorAll('#mainTabs .nav-link').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  if (tab === 'jobs')      loadJobs();
  if (tab === 'companies') loadCompanies();
  if (tab === 'bookmarks') loadBookmarks();
}

// ── Domains dropdown ──────────────────────────────────────────────────────────
async function loadDomains() {
  const { ok, data } = await apiFetch('/api/jobs?per_page=1');
  if (!ok) return;
  const sel = document.getElementById('filterDomain');
  (data.domains || []).forEach(d => {
    const opt = document.createElement('option');
    opt.value = d; opt.textContent = d;
    sel.appendChild(opt);
  });
}

// ── Search debounce ───────────────────────────────────────────────────────────
function debounceSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(applyFilters, 350);
}

function applyFilters() {
  currentPage = 1;
  if (currentTab === 'jobs')      loadJobs();
  if (currentTab === 'companies') loadCompanies();
}

function getFilters() {
  return {
    search:      document.getElementById('searchInput').value.trim(),
    domain:      document.getElementById('filterDomain').value,
    location:    document.getElementById('filterLocation').value,
    job_type:    document.getElementById('filterType').value === 'Internship' ? '' : document.getElementById('filterType').value,
    is_internship: document.getElementById('filterType').value === 'Internship' ? '1' : '',
    salary_min:  document.getElementById('filterSalary').value,
  };
}

// ── Jobs ──────────────────────────────────────────────────────────────────────
async function loadJobs() {
  showSkeleton();
  const f   = getFilters();
  const qs  = new URLSearchParams({
    search: f.search, domain: f.domain, location: f.location,
    job_type: f.job_type, is_internship: f.is_internship,
    salary_min: f.salary_min, page: currentPage, per_page: 12,
  });

  const { ok, data } = await apiFetch(`/api/jobs?${qs}`);
  hideSkeleton();
  if (!ok) { toast('Could not load jobs', 'danger'); return; }

  document.getElementById('resultCount').textContent =
    `Showing ${data.jobs.length} of ${data.total} jobs`;

  const grid = document.getElementById('itemsGrid');
  grid.innerHTML = data.jobs.length
    ? data.jobs.map(j => renderJobCard(j)).join('')
    : '<div class="col-12 text-center text-muted py-5"><i class="bi bi-briefcase fs-1 d-block mb-2"></i>No jobs found</div>';

  renderPagination(data.total_pages);
}

function renderJobCard(j) {
  const salaryStr = j.salary_min && j.salary_max
    ? `₹${j.salary_min}–${j.salary_max} LPA`
    : 'Competitive';

  const skills = (j.skills_list || []).slice(0, 4);
  const colClass = currentLayout === 'grid' ? 'col-md-6 col-lg-4' : 'col-12';
  const internBadge = j.is_internship
    ? '<span class="badge bg-info text-dark ms-1">Internship</span>' : '';
  const bookmarkIcon = j.is_bookmarked
    ? 'bi-bookmark-heart-fill text-warning' : 'bi-bookmark text-muted';

  return `
    <div class="${colClass}">
      <div class="card job-card border-0 shadow-sm h-100 p-4 position-relative"
           onclick="openJobModal(${j.job_id})">
        <button class="btn btn-sm position-absolute top-0 end-0 mt-2 me-2 border-0 bg-transparent bookmark-btn"
                onclick="event.stopPropagation(); quickBookmark(${j.job_id}, this)">
          <i class="bi ${bookmarkIcon} fs-5"></i>
        </button>
        <div class="d-flex gap-3 align-items-start mb-3">
          <div class="company-logo-sm d-flex align-items-center justify-content-center rounded-2 bg-primary bg-opacity-10 flex-shrink-0">
            <i class="bi ${j.logo_icon || 'bi-building'} text-primary fs-4"></i>
          </div>
          <div class="flex-fill" style="min-width:0;">
            <div class="fw-bold text-truncate">${escHtml(j.title)}</div>
            <div class="text-muted small">${escHtml(j.company_name)}</div>
          </div>
        </div>
        <div class="d-flex flex-wrap gap-1 mb-3">
          ${skills.map(s => `<span class="badge bg-light text-dark border" style="font-size:.72rem;">${escHtml(s)}</span>`).join('')}
          ${j.skills_list.length > 4 ? `<span class="badge bg-light text-muted border" style="font-size:.72rem;">+${j.skills_list.length-4}</span>` : ''}
        </div>
        <div class="mt-auto pt-2 border-top">
          <div class="d-flex justify-content-between align-items-center flex-wrap gap-1">
            <div class="small">
              <i class="bi bi-currency-rupee text-success"></i>
              <span class="fw-semibold text-success">${escHtml(salaryStr)}</span>
            </div>
            <div class="d-flex gap-2">
              <span class="badge bg-light text-dark border" style="font-size:.7rem;">
                <i class="bi bi-geo-alt me-1"></i>${escHtml((j.location||'').split('/')[0].trim())}
              </span>
              ${internBadge}
              <span class="badge bg-light text-muted border" style="font-size:.7rem;">
                <i class="bi bi-clock me-1"></i>${j.posted_days_ago}d ago
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>`;
}

// ── Companies ─────────────────────────────────────────────────────────────────
async function loadCompanies() {
  showSkeleton();
  const f  = getFilters();
  const qs = new URLSearchParams({
    search: f.search, page: currentPage, per_page: 12,
  });

  const { ok, data } = await apiFetch(`/api/companies?${qs}`);
  hideSkeleton();
  if (!ok) { toast('Could not load companies', 'danger'); return; }

  document.getElementById('resultCount').textContent =
    `Showing ${data.companies.length} of ${data.total} companies`;

  const colClass = currentLayout === 'grid' ? 'col-md-6 col-lg-4' : 'col-12';
  const grid = document.getElementById('itemsGrid');
  grid.innerHTML = data.companies.length
    ? data.companies.map(c => `
      <div class="${colClass}">
        <div class="card company-card border-0 shadow-sm h-100 p-4"
             onclick="filterByCompany(${c.company_id}, '${escHtml(c.name)}')">
          <div class="d-flex gap-3 align-items-center mb-3">
            <div class="company-logo-sm d-flex align-items-center justify-content-center rounded-2 bg-primary bg-opacity-10 flex-shrink-0">
              <i class="bi ${c.logo_icon || 'bi-building'} text-primary fs-3"></i>
            </div>
            <div>
              <div class="fw-bold">${escHtml(c.name)}</div>
              <div class="text-muted small">${escHtml(c.industry)}</div>
            </div>
          </div>
          <p class="text-muted small mb-3" style="line-clamp:2;-webkit-line-clamp:2;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden;">
            ${escHtml(c.description || '')}
          </p>
          <div class="d-flex gap-2 flex-wrap mt-auto">
            <span class="badge bg-light text-dark border" style="font-size:.72rem;">
              <i class="bi bi-geo-alt me-1"></i>${escHtml((c.location||'').split('/')[0].trim())}
            </span>
            <span class="badge bg-light text-dark border" style="font-size:.72rem;">
              <i class="bi bi-people-fill me-1"></i>${escHtml(c.size||'—')}
            </span>
            <span class="badge bg-primary bg-opacity-10 text-primary" style="font-size:.72rem;">
              <i class="bi bi-briefcase-fill me-1"></i>${c.open_jobs} Jobs
            </span>
            ${c.has_internship ? '<span class="badge bg-info bg-opacity-15 text-info" style="font-size:.72rem;"><i class="bi bi-mortarboard-fill me-1"></i>Internships</span>' : ''}
          </div>
        </div>
      </div>`).join('')
    : '<div class="col-12 text-center text-muted py-5"><i class="bi bi-building fs-1 d-block mb-2"></i>No companies found</div>';

  renderPagination(data.total_pages);
}

function filterByCompany(id, name) {
  currentTab  = 'jobs';
  currentPage = 1;
  document.getElementById('searchInput').value = name;
  document.querySelectorAll('#mainTabs .nav-link').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('#mainTabs .nav-link')[0].classList.add('active');
  loadJobs();
}

// ── Bookmarks ─────────────────────────────────────────────────────────────────
async function loadBookmarks() {
  showSkeleton();
  const { ok, data } = await apiFetch('/api/jobs/bookmarks');
  hideSkeleton();
  if (!ok) { toast('Could not load bookmarks', 'danger'); return; }

  document.getElementById('resultCount').textContent =
    `${data.bookmarks.length} saved job(s)`;

  const colClass = currentLayout === 'grid' ? 'col-md-6 col-lg-4' : 'col-12';
  const grid = document.getElementById('itemsGrid');
  grid.innerHTML = data.bookmarks.length
    ? data.bookmarks.map(j => renderJobCard(j)).join('')
    : `<div class="col-12 text-center text-muted py-5">
        <i class="bi bi-bookmark-heart fs-1 d-block mb-2"></i>
        <div>No saved jobs yet.</div>
        <button class="btn btn-outline-primary mt-3" onclick="switchTab('jobs', document.querySelectorAll('#mainTabs .nav-link')[0])">Browse Jobs</button>
      </div>`;
  document.getElementById('pagination').innerHTML = '';
}

// ── Quick bookmark (from card) ─────────────────────────────────────────────────
async function quickBookmark(jobId, btn) {
  const { ok, data } = await apiFetch(`/api/jobs/${jobId}/bookmark`, { method: 'POST' });
  if (!ok) { toast('Failed to save', 'danger'); return; }
  const icon = btn.querySelector('i');
  icon.className = data.bookmarked
    ? 'bi bi-bookmark-heart-fill text-warning fs-5'
    : 'bi bi-bookmark text-muted fs-5';
  toast(data.bookmarked ? 'Job saved!' : 'Bookmark removed', data.bookmarked ? 'success' : 'info');
}

// ── Job Modal ─────────────────────────────────────────────────────────────────
async function openJobModal(jobId) {
  currentJobId = jobId;
  document.getElementById('modalJobTitle').textContent = 'Loading…';
  document.getElementById('modalCompanyName').textContent = '';
  document.getElementById('modalBody').innerHTML =
    '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';

  new bootstrap.Modal(document.getElementById('jobModal')).show();

  const { ok, data } = await apiFetch(`/api/jobs/${jobId}`);
  if (!ok) { document.getElementById('modalBody').innerHTML = '<p class="text-danger">Could not load job.</p>'; return; }

  const j = data.job;
  document.getElementById('modalJobTitle').textContent    = j.title;
  document.getElementById('modalCompanyName').textContent = j.company_name;
  document.getElementById('modalLogoIcon').className      = `bi ${j.logo_icon || 'bi-building'} fs-2 text-primary`;
  document.getElementById('modalApplyBtn').href           = j.website || '#';

  const bkBtn = document.getElementById('modalBookmarkBtn');
  bkBtn.innerHTML = j.is_bookmarked
    ? '<i class="bi bi-bookmark-heart-fill me-1"></i>Saved'
    : '<i class="bi bi-bookmark me-1"></i>Save Job';
  bkBtn.className = j.is_bookmarked
    ? 'btn btn-warning fw-semibold'
    : 'btn btn-outline-warning';

  const salaryStr = j.salary_min && j.salary_max
    ? `₹${j.salary_min}–${j.salary_max} LPA` : 'Competitive';

  document.getElementById('modalBody').innerHTML = `
    <!-- Meta row -->
    <div class="row g-2 mb-4">
      ${[
        ['bi-geo-alt-fill','Location', j.location || j.company_location || '—', 'primary'],
        ['bi-currency-rupee','Salary', salaryStr, 'success'],
        ['bi-briefcase-fill','Type', j.job_type, 'info'],
        ['bi-clock-fill','Posted', `${j.posted_days_ago}d ago`, 'secondary'],
      ].map(([icon,label,val,color]) => `
        <div class="col-6 col-md-3">
          <div class="card border-0 bg-${color} bg-opacity-10 p-3 text-center h-100">
            <i class="bi ${icon} text-${color} fs-4 mb-1 d-block"></i>
            <div class="text-muted small">${label}</div>
            <div class="fw-bold small">${escHtml(val)}</div>
          </div>
        </div>`).join('')}
    </div>

    <!-- Description -->
    <h6 class="fw-bold">About the Role</h6>
    <p class="text-muted">${escHtml(j.description || 'No description available.')}</p>

    <!-- Skills required -->
    <h6 class="fw-bold mt-3">Required Skills</h6>
    <div class="d-flex flex-wrap gap-2 mb-3">
      ${j.skills_list.map(s => `<span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-3 py-2">${escHtml(s)}</span>`).join('')}
    </div>

    <!-- Company info -->
    <div class="card border-0 bg-light p-3 mb-3">
      <h6 class="fw-bold mb-1"><i class="bi ${j.logo_icon||'bi-building'} text-primary me-2"></i>${escHtml(j.company_name)}</h6>
      <p class="text-muted small mb-1">${escHtml(j.company_desc || '')}</p>
      <div class="d-flex gap-2 flex-wrap">
        <span class="badge bg-light text-dark border"><i class="bi bi-people-fill me-1"></i>${escHtml(j.size||'—')}</span>
        <span class="badge bg-light text-dark border"><i class="bi bi-geo-alt me-1"></i>${escHtml(j.company_location||'—')}</span>
        ${j.has_internship ? '<span class="badge bg-info bg-opacity-15 text-info"><i class="bi bi-mortarboard me-1"></i>Offers Internships</span>' : ''}
      </div>
    </div>

    <!-- Similar jobs -->
    ${j.similar_jobs.length ? `
      <h6 class="fw-bold mt-3">Similar Roles</h6>
      <div class="row g-2">
        ${j.similar_jobs.map(s => `
          <div class="col-md-6">
            <div class="card border-0 bg-light p-2 cursor-pointer" onclick="openJobModal(${s.job_id}); bootstrap.Modal.getInstance(document.getElementById('jobModal')).hide();">
              <div class="fw-semibold small">${escHtml(s.title)}</div>
              <div class="text-muted" style="font-size:.75rem;">${escHtml(s.company_name)} · ₹${s.salary_min||0}–${s.salary_max||0} LPA</div>
            </div>
          </div>`).join('')}
      </div>` : ''}
  `;
}

async function toggleJobBookmark() {
  if (!currentJobId) return;
  const { ok, data } = await apiFetch(`/api/jobs/${currentJobId}/bookmark`, { method: 'POST' });
  if (!ok) return;
  const btn = document.getElementById('modalBookmarkBtn');
  btn.innerHTML = data.bookmarked
    ? '<i class="bi bi-bookmark-heart-fill me-1"></i>Saved'
    : '<i class="bi bi-bookmark me-1"></i>Save Job';
  btn.className = data.bookmarked ? 'btn btn-warning fw-semibold' : 'btn btn-outline-warning';
  toast(data.bookmarked ? 'Job saved!' : 'Bookmark removed', data.bookmarked ? 'success' : 'info');
}

// ── Pagination ────────────────────────────────────────────────────────────────
function renderPagination(totalPages) {
  const nav = document.getElementById('pagination');
  if (totalPages <= 1) { nav.innerHTML = ''; return; }
  let html = '';
  html += `<li class="page-item ${currentPage===1?'disabled':''}">
    <button class="page-link" onclick="goPage(${currentPage-1})"><i class="bi bi-chevron-left"></i></button></li>`;
  for (let p = Math.max(1,currentPage-2); p <= Math.min(totalPages,currentPage+2); p++) {
    html += `<li class="page-item ${p===currentPage?'active':''}">
      <button class="page-link" onclick="goPage(${p})">${p}</button></li>`;
  }
  html += `<li class="page-item ${currentPage===totalPages?'disabled':''}">
    <button class="page-link" onclick="goPage(${currentPage+1})"><i class="bi bi-chevron-right"></i></button></li>`;
  nav.innerHTML = html;
}

function goPage(p) {
  currentPage = p;
  if (currentTab === 'jobs')      loadJobs();
  if (currentTab === 'companies') loadCompanies();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Layout ────────────────────────────────────────────────────────────────────
function setLayout(layout, btn) {
  currentLayout = layout;
  document.querySelectorAll('.layout-btn').forEach(b => {
    b.classList.remove('active','btn-secondary');
    b.classList.add('btn-outline-secondary');
  });
  btn.classList.remove('btn-outline-secondary');
  btn.classList.add('active','btn-secondary');
  if (currentTab === 'jobs')      loadJobs();
  if (currentTab === 'companies') loadCompanies();
}

// ── Skeleton helpers ──────────────────────────────────────────────────────────
function showSkeleton() {
  document.getElementById('itemsGrid').innerHTML = '';
  document.getElementById('skeleton').classList.remove('d-none');
}
function hideSkeleton() {
  document.getElementById('skeleton').classList.add('d-none');
}
