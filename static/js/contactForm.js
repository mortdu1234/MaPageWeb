// ─────────────────────────────────────────────
//  Formulaire de contact  (contact.html)
// ─────────────────────────────────────────────
function handleSubmit(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  btn.textContent = 'Message envoyé ✓';
  btn.style.background = '#5a7a4a';
  btn.disabled = true;
  e.target.reset();
  setTimeout(() => {
    btn.textContent = 'Envoyer le message';
    btn.style.background = '';
    btn.disabled = false;
  }, 4000);
}