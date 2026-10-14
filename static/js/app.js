(function () {
  const root = document.documentElement;

  /* ---- dark mode ---- */
  const themeBtn = document.getElementById('themeToggle');
  const paint = () => { if (themeBtn) themeBtn.textContent = root.dataset.theme === 'dark' ? '☀️' : '🌙'; };
  paint();
  if (themeBtn) themeBtn.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
    paint();
    window.dispatchEvent(new Event('themechange'));      // charts listen for this
  });

  /* ---- responsive menu ---- */
  const toggle = document.getElementById('navToggle'), menu = document.getElementById('menu');
  if (toggle && menu) toggle.addEventListener('click', () => {
    const open = menu.classList.toggle('open');
    toggle.setAttribute('aria-expanded', open);
  });

  /* ---- notifications ---- */
  const box = document.getElementById('toasts');
  function wire(t) {
    const close = () => t.remove();
    t.querySelector('.x').addEventListener('click', close);
    setTimeout(close, 4500);
  }
  if (box) box.querySelectorAll('.toast').forEach(wire);
  window.toast = (msg, type) => {
    if (!box) return;
    const t = document.createElement('div');
    t.className = 'toast ' + (type || 'info');
    t.append(document.createTextNode(msg));
    t.insertAdjacentHTML('beforeend', '<button class="x" aria-label="Dismiss">×</button>');
    box.append(t); wire(t);
  };

  /* ---- delete confirmation ---- */
  const dlg = document.getElementById('deleteDialog');
  if (dlg) {
    document.querySelectorAll('[data-delete-url]').forEach(btn => btn.addEventListener('click', () => {
      document.getElementById('deleteName').textContent = btn.dataset.name;
      document.getElementById('deleteForm').action = btn.dataset.deleteUrl;
      dlg.showModal();
    }));
    document.getElementById('deleteCancel').addEventListener('click', () => dlg.close());
  }

  /* ---- filters: dropdowns apply immediately ---- */
  document.querySelectorAll('form[data-autosubmit] select').forEach(s =>
    s.addEventListener('change', () => s.form.submit()));
})();
