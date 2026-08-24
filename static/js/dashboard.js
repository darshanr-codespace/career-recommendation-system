/* dashboard.js — enhanced with hover cards and Test Your Knowledge CTA */

let allRecs = [];
const GROWTH_ORDER = { 'Very High': 4, 'High': 3, 'Moderate': 2, 'Low': 1 };
let hoverTimer = null;
let loadedHovers = {};

document.addEventListener('DOMContentLoaded', loadRecommendations);

async function loadRecommendations() {
  const btn     = document.getElementById('refreshBtn');
  const spinner = document.getElementById('refreshSpinner');
  const grid    = document.getElementById('cardsGrid');
  const skel    = document.getElementById('skeleton');
  const empty   = document.getElementById('emptyState');
  const alertEl = document.getElementById('dashAlert');

  btn.disabled = true;
  spinner.classList.remove('d-none');
  grid.classList.add('d-none');
  empty.classList.add('d-none');
  skel.classList.remove('d-none');

  const { ok, data } = await apiFetch('/api/recommend');
  btn.disabled = false;
  spinner.classList.add('d-none');
  skel.classList.add('d-none');

  if (!ok) {
    if (data.error === 'incomplete_profile') {
      const missingList = (data.missing_fields || []).map(f => `<li>${f}</li>`).join('');
      alertEl.className = 'alert alert-warning border-0 rounded-3';
      alertEl.innerHTML = `
        <div class="d-flex gap-3 align-items-start">
          <i class="bi bi-exclamation-triangle-fill fs-4 text-warning flex-shrink-0 mt-1"></i>
          <div>
            <div class="fw-bold mb-1">Not enough data to predict careers</div>
            <div class="text-muted small mb-2">${data.message}</div>
            ${missingList ? `<ul class="mb-2 ps-3 small text-muted">${missingList}</ul>` : ''}
            <a href="/profile" class="btn btn-warning btn-sm fw-semibold">
              <i class="bi bi-pencil-fill me-1"></i>Complete Profile
            </a>
          </div>
        </div>`;
      alertEl.classList.remove('d-none');
    } else {
      showAlert(alertEl, 'danger', data.error || 'Could not load recommendations. Please update your profile first.');
    }
    empty.classList.remove('d-none');
    return;
  }

  allRecs = data.recommendations || [];
  if (!allRecs.length) { empty.classList.remove('d-none'); return; }
  renderCards(allRecs);
  grid.classList.remove('d-none');
  const jobsCta = document.getElementById('jobsCta');
  if (jobsCta) jobsCta.style.removeProperty('display');
}

function renderCards(recs) {
  const domainColors = {
    'Information Technology':'primary','Healthcare':'danger','Engineering':'warning',
    'Finance & Commerce':'success','Business':'info','Law':'secondary',
    'Design':'purple','Media & Communication':'pink',
    'Analytics':'primary','Research':'info','Education':'success',
  };
  document.getElementById('cardsGrid').innerHTML = recs.map(r => {
    const color      = domainColors[r.domain] || 'primary';
    const score      = r.compatibility_score;
    const scoreColor = score >= 70 ? '#10B981' : score >= 50 ? '#F59E0B' : '#EF4444';
    const growthIcon = r.growth_rate === 'Very High' ? '🚀' : r.growth_rate === 'High' ? '📈' : '📊';
    const recJson    = JSON.stringify(r).replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'&quot;');

    return `
      <div class="col-md-6 col-lg-4"
           data-score="${score}" data-salary="${r.avg_salary_lpa||0}"
           data-growth="${GROWTH_ORDER[r.growth_rate]||0}">
        <div class="card career-card h-100 border-0 shadow-sm position-relative overflow-hidden"
             onmouseenter="showHoverCard(${r.career_id}, this)"
             onmouseleave="hideHoverCard(this)"
             onclick="openCareerModal(${r.career_id},'${escHtml(r.career_name)}','${escHtml(r.domain)}')">
          <div class="rank-ribbon">#${r.rank}</div>
          <div class="card-body p-4">
            <div class="d-flex justify-content-between align-items-start mb-3">
              <div>
                <h6 class="fw-bold mb-1">${escHtml(r.career_name)}</h6>
                <span class="badge bg-${color} bg-opacity-10 text-${color}">${escHtml(r.domain)}</span>
              </div>
              <div class="text-center flex-shrink-0 ms-2">
                <div class="fw-bold" style="font-size:1.4rem;color:${scoreColor};line-height:1;">${score.toFixed(1)}<span style="font-size:.7rem;">%</span></div>
                <div class="text-muted" style="font-size:.65rem;">Match</div>
              </div>
            </div>
            <p class="text-muted small mb-3" style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
              ${escHtml(r.description||'')}
            </p>
            <div class="d-flex flex-wrap gap-1 mb-3">
              <span class="badge bg-light text-dark border"><i class="bi bi-currency-rupee"></i>${r.avg_salary_lpa} LPA</span>
              <span class="badge bg-light text-dark border">${growthIcon} ${r.growth_rate}</span>
              <span class="badge bg-light text-dark border"><i class="bi bi-building me-1 text-primary"></i>${(r.work_environment||'').split('/')[0]}</span>
            </div>
            <div class="pt-3 border-top">
              ${['content_based','collaborative','random_forest'].map((k,i) => {
                const labels=['Content','Collaborative','RF'];
                return `<div class="d-flex align-items-center gap-2 mb-1">
                  <span style="font-size:.65rem;width:76px;color:#9CA3AF;flex-shrink:0;">${labels[i]}</span>
                  <div class="flex-fill rounded" style="height:4px;background:#F3F4F6;">
                    <div class="rounded" style="height:4px;width:${r.scores[k]}%;background:#2563EB;"></div>
                  </div>
                  <span style="font-size:.65rem;width:28px;text-align:right;color:#6B7280;">${r.scores[k].toFixed(0)}%</span>
                </div>`;
              }).join('')}
            </div>
          </div>
          <div class="card-footer border-0 bg-transparent px-4 pb-3 pt-0">
            <a href="/career/${r.career_id}" class="btn btn-outline-primary btn-sm w-100" onclick="event.stopPropagation()">
              <i class="bi bi-arrow-right-circle me-1"></i>Skill Gap & Career Path
            </a>
          </div>
          <!-- hover overlay -->
          <div class="hover-overlay d-none" id="hover_${r.career_id}">
            <div class="hover-content p-3">
              <div class="fw-bold mb-1 text-white">${escHtml(r.career_name)}</div>
              <div class="hover-loading text-center py-3"><div class="spinner-border spinner-border-sm text-white opacity-75"></div></div>
            </div>
          </div>
        </div>
      </div>`;
  }).join('');
}

// ── Hover card async load ──────────────────────────────────────────────────────
function showHoverCard(careerId, cardEl) {
  hoverTimer = setTimeout(async () => {
    const overlay = document.getElementById(`hover_${careerId}`);
    if (!overlay) return;
    overlay.classList.remove('d-none');
    if (loadedHovers[careerId]) return;

    const { ok, data } = await apiFetch(`/api/skill-gap/${careerId}`);
    if (!ok) { overlay.classList.add('d-none'); return; }
    loadedHovers[careerId] = true;
    const s = data.summary;

    overlay.querySelector('.hover-content').innerHTML = `
      <div class="fw-bold mb-1 text-white fs-6">${escHtml(data.career.career_name)}</div>
      <div class="text-white opacity-75 small mb-3">${escHtml(data.career.domain)}</div>
      <div class="d-flex justify-content-around text-center mb-3">
        <div><div class="fw-bold fs-5 text-warning">${s.readiness_pct}%</div><div style="font-size:.68rem;opacity:.7;">Readiness</div></div>
        <div><div class="fw-bold fs-5 text-success">${s.strengths}</div><div style="font-size:.68rem;opacity:.7;">Strengths</div></div>
        <div><div class="fw-bold fs-5 text-danger">${s.major_gaps}</div><div style="font-size:.68rem;opacity:.7;">Gaps</div></div>
      </div>
      <div class="mb-3">
        <div style="font-size:.68rem;opacity:.65;margin-bottom:3px;" class="text-white">SKILL READINESS</div>
        <div class="progress" style="height:5px;background:rgba(255,255,255,.2);">
          <div class="progress-bar bg-warning" style="width:${s.readiness_pct}%"></div>
        </div>
      </div>
      ${Object.entries(data.resources||{}).slice(0,1).map(([skill,res]) =>
        res[0] ? `<div class="text-white small opacity-75 mb-2"><i class="bi bi-book-fill text-warning me-1"></i>${escHtml(res[0].title)}</div>` : ''
      ).join('')}
      <a href="/career/${careerId}" class="btn btn-sm btn-warning fw-bold w-100 mt-1" onclick="event.stopPropagation()">
        Full Analysis →
      </a>`;
  }, 400);
}

function hideHoverCard(cardEl) {
  clearTimeout(hoverTimer);
  cardEl.querySelectorAll('.hover-overlay').forEach(o => o.classList.add('d-none'));
}

// ── Career Modal ──────────────────────────────────────────────────────────────
async function openCareerModal(id, name, domain) {
  document.getElementById('modalCareerName').textContent = name;
  document.getElementById('modalDomain').textContent     = domain;
  document.getElementById('modalCareerLink').href        = `/career/${id}`;
  document.getElementById('modalBody').innerHTML =
    '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';
  new bootstrap.Modal(document.getElementById('careerModal')).show();

  // Load skill gap for modal
  const { ok, data } = await apiFetch(`/api/skill-gap/${id}`);
  if (!ok) return;
  const s = data.summary;

  // Find rec data
  const rec = allRecs.find(r => r.career_id === id) || {};
  const score      = rec.compatibility_score || 0;
  const scoreColor = score >= 70 ? 'success' : score >= 50 ? 'warning' : 'danger';

  document.getElementById('modalBody').innerHTML = `
    <div class="row g-3 text-center mb-4">
      ${[
        ['Match Score', score.toFixed(1)+'%', scoreColor],
        ['Skill Readiness', s.readiness_pct+'%', 'info'],
        ['Avg Salary', '₹'+(rec.avg_salary_lpa||'—')+' LPA', 'success'],
        ['Growth', rec.growth_rate||'—', 'warning'],
      ].map(([label,val,c]) => `
        <div class="col-6 col-md-3">
          <div class="bg-${c} bg-opacity-10 rounded-3 p-3">
            <div class="fw-bold text-${c}">${escHtml(val)}</div>
            <div class="text-muted small">${label}</div>
          </div>
        </div>`).join('')}
    </div>

    <div class="row g-3 mb-3">
      <div class="col-md-6">
        <div class="card border-0 bg-light p-3 h-100">
          <div class="text-muted small fw-semibold mb-2"><i class="bi bi-check-circle-fill text-success me-1"></i>STRENGTHS</div>
          ${s.strengths > 0
            ? Object.entries(data.gaps).filter(([k,v])=>v.status==='strength').slice(0,5).map(([k])=>`<span class="badge bg-success bg-opacity-10 text-success me-1 mb-1">${escHtml(k)}</span>`).join('')
            : '<span class="text-muted small">Build more skills</span>'}
        </div>
      </div>
      <div class="col-md-6">
        <div class="card border-0 bg-light p-3 h-100">
          <div class="text-muted small fw-semibold mb-2"><i class="bi bi-x-circle-fill text-danger me-1"></i>SKILLS TO BUILD</div>
          ${s.major_gaps > 0
            ? Object.entries(data.gaps).filter(([k,v])=>v.status==='major_gap').slice(0,5).map(([k])=>`<span class="badge bg-danger bg-opacity-10 text-danger me-1 mb-1">${escHtml(k)}</span>`).join('')
            : '<span class="text-muted small">No major gaps! 🎉</span>'}
        </div>
      </div>
    </div>

    <div class="card border-0 bg-light p-3">
      <div class="text-muted small fw-semibold mb-2"><i class="bi bi-lightning-fill text-warning me-1"></i>QUICK ACTIONS</div>
      <div class="d-flex gap-2 flex-wrap">
        <a href="/career/${id}" class="btn btn-sm btn-outline-primary">Detailed Skill Gap</a>
        <a href="/assessment" class="btn btn-sm btn-outline-warning">Test Knowledge</a>
        <a href="/companies?domain=${encodeURIComponent(domain)}" class="btn btn-sm btn-outline-success">Find Jobs</a>
      </div>
    </div>`;
}

// ── Sort ──────────────────────────────────────────────────────────────────────
function sortCards(by, btn) {
  document.querySelectorAll('.sort-btn').forEach(b => b.className = 'btn btn-sm btn-outline-secondary sort-btn');
  if (btn) btn.className = 'btn btn-sm btn-primary sort-btn active';
  const sorted = [...allRecs].sort((a,b) => {
    if (by==='score')  return b.compatibility_score - a.compatibility_score;
    if (by==='salary') return (b.avg_salary_lpa||0) - (a.avg_salary_lpa||0);
    if (by==='growth') return (GROWTH_ORDER[b.growth_rate]||0) - (GROWTH_ORDER[a.growth_rate]||0);
    return 0;
  });
  renderCards(sorted);
  document.getElementById('cardsGrid').classList.remove('d-none');
}
