import { injectCSS } from './Utils.js';
// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//
//  Attributs :
//    root        – chemin racine (défaut : '/')
//    username    – nom affiché si connecté
//    permissions – JSON array de permissions
//    pages       – JSON array de pages { label, href, permission? }
//
//  Comportement :
//    Si les liens ne rentrent plus dans la navbar,
//    les liens en trop sont déplacés dans un menu "···"
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  connectedCallback() {
    injectCSS('nav-bar', 'navbar.css');

    const root        = this.getAttribute('root') || '/';
    const username    = this.getAttribute('username') || '';
    const raw         = this.getAttribute('permissions') || '[]';
    const permissions = JSON.parse(raw);

    const defaultPages = [
      { label: 'Accueil',         href: '/' },
      { label: 'Jeux de société', href: '/jeux', permission: 'showGame' },
      { label: 'À propos',        href: '/apropos' },
      { label: 'Contact',         href: '/contact' },
      { label: 'Mes projets',     href: '/projets' },
    ];

    const rawPages = this.getAttribute('pages');
    const pages    = rawPages ? JSON.parse(rawPages) : defaultPages;

    const visiblePages = pages.filter(page => {
      if (!page.permission) return true;
      return permissions.includes('admin') || permissions.includes(page.permission);
    });

    const authLink = username && username !== 'None'
      ? `<li class="nav-user">
          <span class="nav-username">${username}</span>
          <a href="/logout">Déconnexion</a>
        </li>`
      : `<li><a href="/login">Connexion</a></li>`;

    this.innerHTML = `
      <nav>
        <a class="nav-brand" href="${root}">Denis ROBERT</a>
        <div class="nav-links-wrapper">
          <ul class="nav-links">
            ${visiblePages.map(p => `<li><a href="${p.href}">${p.label}</a></li>`).join('\n            ')}
            ${authLink}
          </ul>
          <button class="nav-more-btn" aria-haspopup="true" aria-expanded="false" aria-label="Plus de pages">
            ···
          </button>
        </div>
        <div class="nav-dropdown"></div>
      </nav>
    `;

    // Marque le lien actif
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    this.querySelectorAll('.nav-links a').forEach(link => {
      const href = link.getAttribute('href').replace(/\/$/, '') || '/';
      if (href === currentPath) link.classList.add('active');
    });

    this._initOverflow();
  }

  _initOverflow() {
    const nav      = this.querySelector('nav');
    const moreBtn  = this.querySelector('.nav-more-btn');
    const dropdown = this.querySelector('.nav-dropdown');

    // Ouvre / ferme le dropdown
    moreBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = dropdown.classList.toggle('open');
      moreBtn.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', () => {
      dropdown.classList.remove('open');
      moreBtn.setAttribute('aria-expanded', 'false');
    });

    // Recalcule à chaque redimensionnement
    const ro = new ResizeObserver(() => this._computeOverflow());
    ro.observe(nav);
    this._computeOverflow();
  }

  _computeOverflow() {
    const list     = this.querySelector('.nav-links');
    const moreBtn  = this.querySelector('.nav-more-btn');
    const dropdown = this.querySelector('.nav-dropdown');
    const wrapper  = this.querySelector('.nav-links-wrapper');

    // Réaffiche tous les éléments pour mesurer
    const items = Array.from(list.querySelectorAll('li'));
    items.forEach(li => { li.style.display = ''; });
    moreBtn.classList.remove('visible');
    dropdown.innerHTML = '';

    const GAP          = 28;   // gap entre les liens (px), doit correspondre au CSS
    const BTN_ESTIMATE = 56;   // largeur estimée du bouton "···"
    const wrapperWidth = wrapper.getBoundingClientRect().width;

    let usedWidth = 0;
    const overflow = [];

    items.forEach((li, i) => {
      const w      = li.getBoundingClientRect().width;
      const offset = i > 0 ? GAP : 0;
      // Si ce n'est pas le dernier élément, réserve la place pour le bouton "···"
      const isLast = i === items.length - 1;
      const limit  = isLast ? wrapperWidth : wrapperWidth - BTN_ESTIMATE - GAP;

      if (usedWidth + offset + w <= limit) {
        usedWidth += offset + w;
      } else {
        overflow.push(li);
      }
    });

    if (overflow.length > 0) {
      overflow.forEach(li => {
        li.style.display = 'none';
        const src = li.querySelector('a');
        if (src) {
          const a = document.createElement('a');
          a.href        = src.getAttribute('href');
          a.textContent = src.textContent;
          if (src.classList.contains('active')) a.classList.add('active');
          dropdown.appendChild(a);
        }
      });
      moreBtn.classList.add('visible');
    }
  }
}

customElements.define('nav-bar', NavBar);