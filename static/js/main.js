'use strict';

// ── Character counters ──────────────────────────────────────────────────────
function setupCounter(fieldId, counterId, max) {
  const field = document.getElementById(fieldId);
  const counter = document.getElementById(counterId);
  if (!field || !counter) return;

  function update() {
    const len = field.value.length;
    counter.textContent = len;
    counter.classList.toggle('text-danger', len >= max);
  }

  field.addEventListener('input', update);
  update();
}

// ── Date auto-formatter (DD/MM/AAAA) ───────────────────────────────────────
function setupDateInput(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;

  input.addEventListener('input', function () {
    let v = this.value.replace(/\D/g, '');
    if (v.length > 2) v = v.slice(0, 2) + '/' + v.slice(2);
    if (v.length > 5) v = v.slice(0, 5) + '/' + v.slice(5, 9);
    this.value = v;
  });
}

// ── Confirm delete ──────────────────────────────────────────────────────────
function confirmDelete() {
  return window.confirm('Tem certeza que deseja excluir esta tarefa? Esta ação não pode ser desfeita.');
}

// ── Auto-dismiss alerts ─────────────────────────────────────────────────────
function autoDismissAlerts(delayMs) {
  setTimeout(function () {
    document.querySelectorAll('.alert.alert-success, .alert.alert-info').forEach(function (el) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    });
  }, delayMs);
}

// ── Init ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  setupCounter('title', 'title-count', 100);
  setupCounter('description', 'desc-count', 500);
  setupDateInput('deadline');
  autoDismissAlerts(5000);
});
