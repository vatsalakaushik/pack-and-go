// frontend/app.js

// set footer year if present
const yearEl = document.getElementById('year');
if (yearEl) {
  yearEl.textContent = new Date().getFullYear();
}

// hero blur on hover for "Open Dashboard" button
const heroBg = document.getElementById('heroBg');
const openDashBtn = document.querySelector('.big-btn');

if (heroBg && openDashBtn) {
  openDashBtn.addEventListener('mouseenter', () => {
    heroBg.classList.add('blurred');
  });
  openDashBtn.addEventListener('mouseleave', () => {
    heroBg.classList.remove('blurred');
  });
}

// Modal: "What's the dashboard?"
const explainBtn = document.getElementById('explainBtn');
const explainModal = document.getElementById('explainModal');
const closeExplain = document.getElementById('closeExplain');

function openExplain() {
  if (!explainModal) return;
  explainModal.setAttribute('aria-hidden','false');
  explainModal.style.display = 'flex';
  if (closeExplain) closeExplain.focus();
}

function closeExplainModal() {
  if (!explainModal) return;
  explainModal.setAttribute('aria-hidden','true');
  explainModal.style.display = 'none';
  if (explainBtn) explainBtn.focus();
}

if (explainBtn) {
  explainBtn.addEventListener('click', openExplain);
}

if (closeExplain) {
  closeExplain.addEventListener('click', closeExplainModal);
}

if (explainModal) {
  explainModal.addEventListener('click', (e)=>{
    if (e.target === explainModal) closeExplainModal();
  });
}

document.addEventListener('keydown', (e)=>{
  if (e.key === 'Escape' && explainModal && explainModal.getAttribute('aria-hidden') === 'false') {
    closeExplainModal();
  }
});
