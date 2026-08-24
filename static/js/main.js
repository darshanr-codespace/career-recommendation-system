/* main.js — shared utilities */

function showAlert(el, type, msg) {
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.innerHTML = `<i class="bi bi-exclamation-circle-fill me-2"></i>${msg}`;
  el.classList.remove('d-none');
  setTimeout(() => el.classList.add('d-none'), 5000);
}

function toast(msg, type = 'success') {
  const id  = 'toast_' + Date.now();
  const icons = { success:'bi-check-circle-fill', danger:'bi-x-circle-fill', warning:'bi-exclamation-triangle-fill', info:'bi-info-circle-fill' };
  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0 show" role="alert">
      <div class="d-flex">
        <div class="toast-body"><i class="bi ${icons[type]||'bi-bell-fill'} me-2"></i>${msg}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="document.getElementById('${id}').remove()"></button>
      </div>
    </div>`;
  const container = document.getElementById('toastContainer');
  if (container) {
    container.insertAdjacentHTML('beforeend', html);
    setTimeout(() => { const t = document.getElementById(id); if(t) t.remove(); }, 4000);
  }
}

async function apiFetch(url, options = {}) {
  try {
    const res  = await fetch(url, options);
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    console.error('apiFetch error', url, e);
    return { ok: false, status: 0, data: { error: 'Network error' } };
  }
}

function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
