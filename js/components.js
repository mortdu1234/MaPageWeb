// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//  Attribut "root" : chemin vers la racine du site
//  ex: <nav-bar root="./"></nav-bar>        (pages racine)
//      <nav-bar root="../"></nav-bar>       (pages dans sous-dossiers)
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  connectedCallback() {
    const root = this.getAttribute('root') || './';

    this.innerHTML = `
      <nav>
        <a class="nav-brand" href="${root}index.html">Denis ROBERT</a>
        <ul class="nav-links">
          <li><a href="${root}index.html">Accueil</a></li>
          <li><a href="${root}jeux.html">Jeux de société</a></li>
          <li><a href="${root}apropos.html">À propos</a></li>
          <li><a href="${root}contact.html">Contact</a></li>
          <li><a href="${root}mesprojets.html">Mes projets</a></li>
        </ul>
      </nav>
    `;

    // Lien actif : compare l'URL courante avec chaque lien
    const currentFile = window.location.pathname.split('/').pop() || 'index.html';
    this.querySelectorAll('.nav-links a').forEach(link => {
      const linkFile = link.getAttribute('href').split('/').pop();
      if (linkFile === currentFile) link.classList.add('active');
    });
  }
}

// ─────────────────────────────────────────────
//  <site-footer></site-footer>
// ─────────────────────────────────────────────
class SiteFooter extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <footer>
        <span class="brand">Denis ROBERT</span>
      </footer>
    `;
  }
}

// Enregistrement des composants
customElements.define('nav-bar', NavBar);
customElements.define('site-footer', SiteFooter);

// ─────────────────────────────────────────────
//  Formulaire de contact (utilisé sur contact.html)
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
