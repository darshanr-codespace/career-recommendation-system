/* assessment.js */
let questions = [];
let answers   = [];
let current   = 0;
let radarChart= null;

async function startAssessment() {
  document.getElementById('landingView').classList.add('d-none');
  document.getElementById('quizView').classList.remove('d-none');

  const { ok, data } = await apiFetch('/api/assessment/questions');
  if (!ok) { toast('Could not load questions', 'danger'); return; }

  questions = data.questions;
  answers   = new Array(questions.length).fill(null);
  document.getElementById('qTotal').textContent = questions.length;
  showQuestion(0);
}

function showQuestion(idx) {
  const q = questions[idx];
  current  = idx;

  document.getElementById('qCurrent').textContent  = idx + 1;
  document.getElementById('qDomainBadge').textContent = q.domain;
  document.getElementById('qLevelBadge').textContent  = q.level;
  document.getElementById('questionText').textContent = q.question;

  const pct = ((idx + 1) / questions.length) * 100;
  document.getElementById('quizProgress').style.width = pct + '%';

  const grid = document.getElementById('optionsGrid');
  grid.innerHTML = q.options.map((opt, i) => `
    <div class="col-md-6">
      <div class="option-card p-3 rounded-3 border cursor-pointer ${answers[idx]===i?'selected-opt':''}"
           onclick="selectAnswer(${i}, this)">
        <div class="d-flex gap-3 align-items-center">
          <div class="opt-letter">${String.fromCharCode(65+i)}</div>
          <div>${escHtml(opt)}</div>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('prevQBtn').disabled = idx === 0;
  const isLast = idx === questions.length - 1;
  document.getElementById('nextQBtn').classList.toggle('d-none', isLast);
  document.getElementById('submitQBtn').classList.toggle('d-none', !isLast);
}

function selectAnswer(i, el) {
  answers[current] = i;
  document.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected-opt'));
  el.classList.add('selected-opt');
}

function nextQuestion() {
  if (current < questions.length - 1) showQuestion(current + 1);
}

function prevQuestion() {
  if (current > 0) showQuestion(current - 1);
}

async function submitAssessment() {
  const unanswered = answers.filter(a => a === null).length;
  if (unanswered > 0) {
    toast(`${unanswered} question(s) unanswered. You can still submit.`, 'warning');
  }

  const spinner = document.getElementById('submitQSpinner');
  spinner.classList.remove('d-none');
  document.getElementById('submitQBtn').disabled = true;

  const { ok, data } = await apiFetch('/api/assessment/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ answers: answers.map(a => a === null ? 0 : a) }),
  });

  spinner.classList.add('d-none');
  if (!ok) { toast(data.error || 'Submission failed', 'danger'); return; }

  showResults(data);
}

function showResults(data) {
  document.getElementById('quizView').classList.add('d-none');
  document.getElementById('resultsView').classList.remove('d-none');

  document.getElementById('overallScore').textContent = data.overall_score + '%';

  // Domain score bars
  const dsEl = document.getElementById('domainScores');
  dsEl.innerHTML = Object.entries(data.domain_scores).map(([domain, pct]) => {
    const color = pct >= 70 ? 'success' : pct >= 50 ? 'warning' : 'danger';
    return `
      <div class="mb-3">
        <div class="d-flex justify-content-between mb-1">
          <span class="small fw-semibold">${escHtml(domain)}</span>
          <span class="small text-${color} fw-bold">${pct}%</span>
        </div>
        <div class="progress" style="height:8px;">
          <div class="progress-bar bg-${color}" style="width:${pct}%"></div>
        </div>
      </div>`;
  }).join('');

  // Radar chart
  const domains = Object.keys(data.domain_scores);
  const scores  = Object.values(data.domain_scores);
  const ctx = document.getElementById('assessRadar').getContext('2d');
  if (radarChart) radarChart.destroy();
  radarChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: domains,
      datasets: [{
        label: 'Your Score',
        data: scores,
        backgroundColor: 'rgba(37,99,235,0.15)',
        borderColor: '#2563EB',
        pointBackgroundColor: '#2563EB',
      }]
    },
    options: {
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 25 } } },
      plugins: { legend: { display: false } }
    }
  });

  // Strengths & weak areas
  document.getElementById('strengthsList').innerHTML = (data.strengths.length
    ? data.strengths.map(s => `<span class="badge bg-success">${escHtml(s)}</span>`).join('')
    : '<span class="text-muted small">Keep practising!</span>');

  document.getElementById('weakList').innerHTML = (data.weak_areas.length
    ? data.weak_areas.map(s => `<span class="badge bg-danger">${escHtml(s)}</span>`).join('')
    : '<span class="text-muted small">No major weak areas 🎉</span>');

  // Career readiness
  document.getElementById('readinessScore').textContent = data.career_readiness.readiness + '%';
  document.getElementById('readinessCareer').textContent = 'for ' + data.career_readiness.career;

  // Recommendations
  const recEl = document.getElementById('recommendationsSection');
  if (data.weak_areas.length) {
    let html = '<h6 class="fw-bold mb-3"><i class="bi bi-lightbulb-fill text-warning me-2"></i>Recommended Learning Resources</h6><div class="row g-3">';
    for (const [domain, rec] of Object.entries(data.recommendations)) {
      html += `
        <div class="col-md-6">
          <div class="card border-0 bg-light p-3 h-100">
            <div class="fw-bold small mb-2 text-danger"><i class="bi bi-exclamation-triangle-fill me-1"></i>${escHtml(domain)}</div>
            <div class="mb-2">
              <div class="text-muted" style="font-size:.75rem;">CERTIFICATIONS</div>
              ${rec.certs.map(c => `<div class="badge bg-primary bg-opacity-10 text-primary me-1 mb-1">${escHtml(c)}</div>`).join('')}
            </div>
            <div class="mb-2">
              <div class="text-muted" style="font-size:.75rem;">SKILLS TO LEARN</div>
              ${rec.skills.map(s => `<div class="badge bg-success bg-opacity-10 text-success me-1 mb-1">${escHtml(s)}</div>`).join('')}
            </div>
          </div>
        </div>`;
    }
    recEl.innerHTML = html + '</div>';
  } else {
    recEl.innerHTML = '<div class="text-center text-success py-3"><i class="bi bi-check-circle-fill fs-1 d-block mb-2"></i><strong>Excellent!</strong> No major skill gaps detected.</div>';
  }
}

function retakeAssessment() {
  document.getElementById('resultsView').classList.add('d-none');
  document.getElementById('landingView').classList.remove('d-none');
  questions = []; answers = []; current = 0;
}
