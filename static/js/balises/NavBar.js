import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//
//  Attributs :
//    root      – chemin racine (défaut : '/')
//    username  – nom affiché si connecté
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  connectedCallback() {
    injectCSS('nav-bar', 'navbar.css');

    const root = this.getAttribute('root') || '/';
    const username = this.getAttribute('username') || null;

    const authLink = username
      ? `<li class="nav-user">
          <span class="nav-username">${username}</span>
          <a href="/logout">Déconnexion</a>
        </li>`
      : `<li><a href="/login">Connexion</a></li>`;

    this.innerHTML = `
      <nav>
        <a class="nav-brand" href="/">Denis ROBERT</a>
        <ul class="nav-links">
          <li><a href="/">Accueil</a></li>
          <li><a href="/jeux">Jeux de société</a></li>
          <li><a href="/apropos">À propos</a></li>
          <li><a href="/contact">Contact</a></li>
          <li><a href="/projets">Mes projets</a></li>
          ${authLink}
        </ul>
      </nav>
    `;

    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    this.querySelectorAll('.nav-links a').forEach(link => {
      const href = link.getAttribute('href').replace(/\/$/, '') || '/';
      if (href === currentPath) link.classList.add('active');
    });
  }
}

customElements.define('nav-bar', NavBar);