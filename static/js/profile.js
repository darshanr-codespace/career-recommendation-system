/* profile.js — multi-step wizard logic */

let currentStep = 1;
const TOTAL_STEPS = 5;

// State
const state = {
  academic_records: {},
  skills: [],
  interests: [],
  personality_type: null,
};

// ── Navigation ────────────────────────────────────────────────────────────────
function navigate(dir) {
  const next = currentStep + dir;
  if (next < 1 || next > TOTAL_STEPS) return;

  document.getElementById(`step${currentStep}`).classList.add('d-none');
  currentStep = next;
  document.getElementById(`step${currentStep}`).classList.remove('d-none');

  updateProgress();
  updateButtons();
}

function updateProgress() {
  const pct = (currentStep / TOTAL_STEPS) * 100;
  document.getElementById('progressBar').style.width = pct + '%';
  document.getElementById('stepLabel').textContent = `Step ${currentStep} of ${TOTAL_STEPS}`;
}

function updateButtons() {
  document.getElementById('prevBtn').classList.toggle('d-none', currentStep === 1);
  document.getElementById('nextBtn').classList.toggle('d-none', currentStep === TOTAL_STEPS);
  document.getElementById('submitBtn').classList.toggle('d-none', currentStep !== TOTAL_STEPS);
}

// ── Skill rating buttons ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Skill rating click
  document.querySelectorAll('.skill-rating').forEach(group => {
    group.querySelectorAll('.rating-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        group.querySelectorAll('.rating-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });
  });

  // Interest sliders
  document.querySelectorAll('.interest-slider').forEach(slider => {
    slider.addEventListener('input', () => {
      slider.nextElementSibling.textContent = slider.value;
    });
  });

  updateButtons();
});

// ── RIASEC selection ───────────────────────────────────────────────────────────
function selectRiasec(el) {
  document.querySelectorAll('.riasec-option').forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  state.personality_type = el.dataset.code;
}

// ── Collect state ──────────────────────────────────────────────────────────────
function collectState() {
  // Academic
  document.querySelectorAll('[data-subject]').forEach(inp => {
    const val = parseFloat(inp.value);
    if (!isNaN(val)) state.academic_records[inp.dataset.subject] = val;
  });

  // Skills
  state.skills = [];
  document.querySelectorAll('.skill-rating').forEach(group => {
    const selected = group.querySelector('.rating-btn.selected');
    if (selected) {
      state.skills.push({
        skill_name:  group.dataset.skill,
        proficiency: parseInt(selected.dataset.val),
        category:    group.dataset.category,
      });
    }
  });

  // Interests
  state.interests = [];
  document.querySelectorAll('.interest-slider').forEach(slider => {
    state.interests.push({
      domain: slider.dataset.domain,
      interest_score: parseInt(slider.value),
    });
  });
}

// ── Submit ────────────────────────────────────────────────────────────────────
async function submitProfile() {
  const alertBox = document.getElementById('alertBox');
  const btn      = document.getElementById('submitBtn');
  const spinner  = document.getElementById('submitSpinner');

  collectState();

  if (!state.personality_type) {
    showAlert(alertBox, 'warning', 'Please select a personality type.');
    return;
  }

  btn.disabled = true;
  spinner.classList.remove('d-none');

  const payload = {
    academic_records: state.academic_records,
    skills:           state.skills,
    interests:        state.interests,
    personality_type: state.personality_type,
  };

  const { ok, data } = await apiFetch('/auth/profile/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  btn.disabled = false;
  spinner.classList.add('d-none');

  if (ok) {
    showAlert(alertBox, 'success', 'Profile saved! Redirecting to your dashboard…');
    setTimeout(() => window.location.href = '/dashboard', 1200);
  } else {
    showAlert(alertBox, 'danger', data.error || 'Failed to save profile.');
  }
}
