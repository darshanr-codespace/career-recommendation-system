
// ── Onboarding banner ─────────────────────────────────────────────────────────
async function checkAndShowOnboarding() {
  const banner = document.getElementById('onboardingBanner');
  if (!banner) return;

  const { ok, data } = await apiFetch('/auth/profile/completeness');
  if (!ok) return;

  if (!data.is_complete) {
    banner.classList.remove('d-none');
    const badgesEl = document.getElementById('missingFieldsBadges');
    if (badgesEl) {
      const labels = {
        'highest_qualification': '🎓 Highest Qualification',
        'interests':             '❤️ Career Interests',
        'career_goal':           '🎯 Career Goal',
      };
      badgesEl.innerHTML = data.missing.map(f =>
        `<span class="badge bg-danger bg-opacity-15 text-danger border border-danger border-opacity-25 px-2 py-1">${labels[f] || f}</span>`
      ).join('');
    }
  } else {
    banner.classList.add('d-none');
  }
}

/* profile_v2.js — new smart profile system */

let skills = [];
let interests = [];
let experiences = [];
let personality = null;

document.addEventListener('DOMContentLoaded', loadCurrentProfile);

// ── Load existing profile ─────────────────────────────────────────────────────
async function loadCurrentProfile() {
  const { ok, data } = await apiFetch('/auth/me');
  if (!ok) return;

  document.getElementById('pName').value          = data.name            || '';
  document.getElementById('pEdu').value           = data.education_level  || '';
  document.getElementById('pAge').value           = data.age              || '';
  document.getElementById('pGender').value        = data.gender           || '';
  document.getElementById('pQualification').value = data.highest_qualification || '';
  document.getElementById('pSpecialization').value= data.specialization   || '';
  document.getElementById('pCareerGoal').value    = data.career_goal      || '';
  updatePreview();

  // Onboarding banner for new users
  const isNew = new URLSearchParams(window.location.search).get('new') === '1';
  if (isNew) {
    checkAndShowOnboarding();
  }

  // Load skills
  const sr = await apiFetch('/auth/profile/skills');
  if (sr.ok && sr.data.skills) {
    skills = sr.data.skills.map(s => s.skill_name);
    renderSkillTags();
  }

  // Load interests
  const ir = await apiFetch('/auth/profile/interests');
  if (ir.ok && ir.data.interests) {
    interests = ir.data.interests.map(i => i.domain);
    renderInterests();
  }

  // Load resume data
  const rr = await apiFetch('/api/resume/data');
  if (rr.ok && rr.data.data) {
    document.getElementById('uploadStatus').classList.remove('d-none');
    document.getElementById('uploadedFileName').textContent = rr.data.data.filename || 'resume';
  }
}

// ── Resume upload ─────────────────────────────────────────────────────────────
function handleDrop(e) {
  e.preventDefault();
  document.getElementById('dropZone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) uploadResume(file);
}

async function uploadResume(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['pdf','docx','doc'].includes(ext)) { toast('Only PDF and DOCX files supported', 'danger'); return; }
  if (file.size > 5 * 1024 * 1024) { toast('File too large. Max 5MB', 'danger'); return; }

  document.getElementById('uploadProgress').classList.remove('d-none');
  document.getElementById('uploadStatus').classList.add('d-none');

  const form = new FormData();
  form.append('resume', file);

  const { ok, data } = await apiFetch('/api/resume/upload', { method: 'POST', body: form });
  document.getElementById('uploadProgress').classList.add('d-none');

  if (!ok) { toast(data.error || 'Upload failed', 'danger'); return; }

  const parsed = data.parsed;
  document.getElementById('uploadStatus').classList.remove('d-none');
  document.getElementById('uploadedFileName').textContent = file.name;

  // Auto-fill skills
  if (parsed.skills && parsed.skills.length) {
    parsed.skills.forEach(s => { if (!skills.includes(s)) skills.push(s); });
    renderSkillTags();
  }
  // Auto-fill education hint
  if (parsed.education && parsed.education.length) {
    toast(`Resume parsed! Found ${parsed.skills.length} skills, ${parsed.education.length} education entries`, 'success');
  } else {
    toast(`Resume uploaded! Found ${parsed.skills.length} skills`, 'success');
  }

  // Show parsed data summary
  if (parsed.error) toast(parsed.error, 'warning');

  updatePreview();
}

// ── Skills ────────────────────────────────────────────────────────────────────
function addSkill() {
  const input = document.getElementById('skillInput');
  const val = input.value.trim().replace(/,$/, '');
  if (!val) return;
  val.split(',').forEach(s => {
    const skill = s.trim();
    if (skill && !skills.includes(skill)) { skills.push(skill); }
  });
  input.value = '';
  renderSkillTags();
  updatePreview();
}

function removeSkill(skill) {
  skills = skills.filter(s => s !== skill);
  renderSkillTags();
  updatePreview();
}

function renderSkillTags() {
  const container = document.getElementById('skillTags');
  container.innerHTML = skills.map(s => `
    <span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 py-2 px-3 d-flex align-items-center gap-1" style="font-size:.8rem;">
      ${escHtml(s)}
      <button type="button" class="btn-close btn-close" style="font-size:.6rem;" onclick="removeSkill('${escHtml(s)}')"></button>
    </span>
  `).join('');
  if (!skills.length) container.innerHTML = '<span class="text-muted small">No skills added yet</span>';
}

// ── Interests ─────────────────────────────────────────────────────────────────
function toggleInterest(btn) {
  const domain = btn.dataset.domain;
  if (interests.includes(domain)) {
    interests = interests.filter(i => i !== domain);
    btn.classList.remove('btn-primary');
    btn.classList.add('btn-outline-secondary');
  } else {
    interests.push(domain);
    btn.classList.remove('btn-outline-secondary');
    btn.classList.add('btn-primary');
  }
  updatePreview();
}

function renderInterests() {
  document.querySelectorAll('.interest-toggle').forEach(btn => {
    if (interests.includes(btn.dataset.domain)) {
      btn.classList.remove('btn-outline-secondary');
      btn.classList.add('btn-primary');
    }
  });
  updatePreview();
}

// ── Experience rows ───────────────────────────────────────────────────────────
function addExpRow(title='', company='', duration='') {
  const id  = Date.now();
  const div = document.createElement('div');
  div.className = 'card border-0 bg-light p-3 mb-2';
  div.id = `exp_${id}`;
  div.innerHTML = `
    <div class="row g-2">
      <div class="col-md-4"><input type="text" class="form-control form-control-sm" placeholder="Job Title" value="${escHtml(title)}"></div>
      <div class="col-md-4"><input type="text" class="form-control form-control-sm" placeholder="Company" value="${escHtml(company)}"></div>
      <div class="col-md-3"><input type="text" class="form-control form-control-sm" placeholder="Duration e.g. 2022-2023" value="${escHtml(duration)}"></div>
      <div class="col-md-1 d-flex align-items-center">
        <button class="btn btn-sm btn-outline-danger" onclick="document.getElementById('exp_${id}').remove()">
          <i class="bi bi-trash3-fill"></i>
        </button>
      </div>
    </div>`;
  document.getElementById('expList').appendChild(div);
}

// ── Personality ───────────────────────────────────────────────────────────────
function selectPersonality(btn) {
  document.querySelectorAll('.riasec-btn').forEach(b => {
    b.classList.remove('btn-primary');
    b.classList.add('btn-outline-secondary');
  });
  btn.classList.remove('btn-outline-secondary');
  btn.classList.add('btn-primary');
  personality = btn.dataset.code;
}

// ── Live preview ──────────────────────────────────────────────────────────────
function updatePreview() {
  const name  = document.getElementById('pName').value || '—';
  const qual  = document.getElementById('pQualification')?.value || '';
  const edu   = document.getElementById('pEdu').value  || '';
  const goal  = document.getElementById('pCareerGoal')?.value || '';

  document.getElementById('previewName').textContent = name;
  document.getElementById('previewEdu').textContent  = qual || edu || '—';

  const skillEl = document.getElementById('previewSkills');
  skillEl.innerHTML = skills.slice(0,8).map(s =>
    `<span class="badge bg-primary bg-opacity-10 text-primary" style="font-size:.7rem;">${escHtml(s)}</span>`
  ).join('') + (skills.length > 8 ? `<span class="badge bg-secondary bg-opacity-10 text-muted" style="font-size:.7rem;">+${skills.length-8} more</span>` : '');

  const intEl = document.getElementById('previewInterests');
  intEl.innerHTML = interests.map(i =>
    `<span class="badge bg-success bg-opacity-10 text-success" style="font-size:.7rem;">${escHtml(i)}</span>`
  ).join('');

  const goalEl = document.getElementById('previewGoal');
  if (goalEl) goalEl.textContent = goal || '—';
}

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveProfile() {
  const btn     = document.querySelector('[onclick="saveProfile()"]');
  const spinner = document.getElementById('saveSpinner');
  btn.disabled  = true;
  spinner.classList.remove('d-none');

  // Collect experience rows
  const expItems = [];
  document.querySelectorAll('#expList .card').forEach(row => {
    const inputs = row.querySelectorAll('input');
    if (inputs[0].value.trim()) {
      expItems.push({ title: inputs[0].value, company: inputs[1].value, duration: inputs[2].value });
    }
  });

  const qual  = document.getElementById('pQualification')?.value || '';
  const spec  = document.getElementById('pSpecialization')?.value || '';
  const goal  = document.getElementById('pCareerGoal')?.value || '';

  // Validate required fields
  const hasEdu       = document.getElementById('pEdu').value || qual;
  const hasInterests = interests.length > 0;
  const hasGoal      = goal.trim();
  const missing = [];
  if (!hasEdu)       missing.push('Highest Qualification');
  if (!hasInterests) missing.push('Career Interests');
  if (!hasGoal)      missing.push('Career Goal');

  if (missing.length) {
    btn.disabled = false;
    spinner.classList.add('d-none');
    toast('Please fill in: ' + missing.join(', '), 'danger');
    checkAndShowOnboarding();
    return;
  }

  const payload = {
    name:                    document.getElementById('pName').value,
    education_level:         document.getElementById('pEdu').value,
    highest_qualification:   qual,
    specialization:          spec,
    career_goal:             goal,
    age:                     document.getElementById('pAge').value || null,
    gender:                  document.getElementById('pGender').value,
    personality_type:        personality,
    skills:                  skills.map(s => ({ skill_name: s, proficiency: 3, category: 'technical' })),
    interests:               interests.map(d => ({ domain: d, interest_score: 7 })),
    experiences:             expItems,
  };

  const { ok, data } = await apiFetch('/auth/profile/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  btn.disabled = false;
  spinner.classList.add('d-none');

  if (ok) {
    const isNew = new URLSearchParams(window.location.search).get('new') === '1';
    toast('Profile saved! Redirecting to dashboard…', 'success');
    setTimeout(() => {
      window.location.href = isNew ? '/dashboard' : '/profile';
    }, 1200);
  } else {
    toast(data.error || 'Failed to save profile', 'danger');
  }
}
