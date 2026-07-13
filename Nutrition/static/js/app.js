/* NutriAgent AI — JavaScript Core */

'use strict';

// ── Dark Mode ──────────────────────────────────────────────────────
const html = document.documentElement;

document.addEventListener('DOMContentLoaded', () => {
  // Sync toggle button with current theme
  const saved = localStorage.getItem('nutriagent_theme');
  if (saved) html.setAttribute('data-theme', saved);

  const toggle = document.getElementById('darkModeToggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const isDark = html.getAttribute('data-theme') === 'dark';
      const next   = isDark ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('nutriagent_theme', next);
      // Persist to server if logged in
      fetch('/api/preferences', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dark_mode: next === 'dark' })
      }).catch(() => {});
    });
  }

  // Sync profile dark_mode checkbox
  const profileCheck = document.getElementById('darkModeProfile');
  if (profileCheck) {
    profileCheck.addEventListener('change', () => {
      html.setAttribute('data-theme', profileCheck.checked ? 'dark' : 'light');
      localStorage.setItem('nutriagent_theme', profileCheck.checked ? 'dark' : 'light');
    });
  }

  // Chart.js dark mode defaults
  updateChartDefaults();

  // Auto-close nav on mobile link click
  document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
    link.addEventListener('click', () => {
      const nav = document.getElementById('navContent');
      if (nav && nav.classList.contains('show')) {
        bootstrap.Collapse.getInstance(nav)?.hide();
      }
    });
  });
});

// Observer for theme changes → update charts
const themeObserver = new MutationObserver(updateChartDefaults);
themeObserver.observe(html, { attributes: true, attributeFilter: ['data-theme'] });

function updateChartDefaults() {
  if (typeof Chart === 'undefined') return;
  const isDark = html.getAttribute('data-theme') === 'dark';
  Chart.defaults.color         = isDark ? '#8b949e' : '#57606a';
  Chart.defaults.borderColor   = isDark ? '#30363d' : '#e5e7eb';
  Chart.defaults.backgroundColor = isDark ? '#161b22' : '#f7f8fa';
}

// ── Toast Notifications ────────────────────────────────────────────
window.showToast = function(message, type = 'success') {
  const container = document.getElementById('flashContainer');
  if (!container) return;

  const icons = { success: 'check-circle-fill', danger: 'exclamation-triangle-fill',
                  warning: 'exclamation-circle-fill', info: 'info-circle-fill' };
  const id    = 'toast-' + Date.now();
  const html  = `
    <div id="${id}" class="alert alert-${type} alert-dismissible fade show alert-toast" role="alert">
      <i class="bi bi-${icons[type] || icons.info} me-2"></i>${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
  container.insertAdjacentHTML('beforeend', html);
  setTimeout(() => {
    const el = document.getElementById(id);
    if (el) bootstrap.Alert.getOrCreateInstance(el).close();
  }, 4500);
};

// ── CSRF helper (for future forms) ────────────────────────────────
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// ── Active nav highlighting ────────────────────────────────────────
document.querySelectorAll('.nav-icon-link').forEach(link => {
  if (link.href === window.location.href) link.classList.add('active');
});

// ── Lazy-load image placeholder ────────────────────────────────────
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.src = e.target.dataset.src; observer.unobserve(e.target); } });
  });
  document.querySelectorAll('img[data-src]').forEach(img => observer.observe(img));
}
