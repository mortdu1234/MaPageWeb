import { injectCSS } from './Utils.js';
// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//
//  Attributs :
//    root        – chemin racine (défaut : '/')
//    username    – nom affiché si connecté
//    permissions – JSON array de permissions
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  connectedCallback() {
    injectCSS('nav-bar', 'navbar.css');
 
    const root        = this.getAttribute('root') || '/';
    const username    = this.getAttribute('username') || '';
    const raw = this.getAttribute('permissions') || '[]';
    const permissions = JSON.parse(raw);
 
    const authLink = username && username !== 'None'
      ? `<li class="nav-user">
          <span class="nav-username">${username}</span>
          <a href="/logout">Déconnexion</a>
        </li>`
      : `<li><a href="/login">Connexion</a></li>`;
 
    const showJeux = permissions.includes('admin') || permissions.includes('showGame');
 
    this.innerHTML = `
      <nav>
        <a class="nav-brand" href="${root}">Denis ROBERT</a>
        <ul class="nav-links">
          <li><a href="/">Accueil</a></li>
          ${showJeux ? `<li><a href="/jeux">Jeux de société</a></li>` : ''}
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