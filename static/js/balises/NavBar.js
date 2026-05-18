import { injectCSS } from './Utils.js';
// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//
//  Attributs :
//    root        – chemin racine (défaut : '/')
//    username    – nom affiché si connecté
//    permissions – JSON array de permissions
//    pages       – JSON array de pages { label, href, permission? }
//    pages-url   – URL vers un fichier JSON de pages (défaut : './navBar.json')
//
//  Comportement :
//    • ≤ 640px  : hamburger animé → panneau plein écran
//    • > 640px  : liens inline ; débordement → menu "···"
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  async connectedCallback() {
    injectCSS('nav-bar', 'navbar.css');
    injectCSS('nav-bar-responsive', 'responsive.css');

    const root        = this.getAttribute('root') || '/';
    const username    = this.getAttribute('username') || '';
    const raw         = this.getAttribute('permissions') || '[]';
    const permissions = JSON.parse(raw);


    // Récupère les pages depuis l'attribut ou le fichier JSON
    const pagesUrl = this.getAttribute('pages-url');
    const res = await fetch(pagesUrl);
    let pages = await res.json();

    const visiblePages = pages.filter(page => {
      if (!page.permission) return true;
      return permissions.some(p => page.permission.includes(p));
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

          <!-- Bouton overflow desktop (···) -->
          <button class="nav-more-btn" aria-haspopup="true" aria-expanded="false" aria-label="Plus de pages">
            ···
          </button>
        </div>

        <!-- Dropdown overflow desktop -->
        <div class="nav-dropdown"></div>

        <!-- Bouton hamburger mobile -->
        <button class="nav-hamburger" aria-label="Ouvrir le menu" aria-expanded="false">
          <span></span>
          <span></span>
          <span></span>
        </button>
      </nav>
    `;

    // Marque le lien actif
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    this.querySelectorAll('.nav-links a').forEach(link => {
      const href = link.getAttribute('href').replace(/\/$/, '') || '/';
      if (href === currentPath) link.classList.add('active');
    });

    this._initHamburger();
    this._initOverflow();
  }

  /* ── Hamburger mobile ───────────────────────────────────── */
  _initHamburger() {
    const hamburger    = this.querySelector('.nav-hamburger');
    const linksWrapper = this.querySelector('.nav-links-wrapper');

    const open = () => {
      linksWrapper.classList.add('open');
      hamburger.classList.add('open');
      hamburger.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    };

    const close = () => {
      linksWrapper.classList.remove('open');
      hamburger.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    };

    hamburger.addEventListener('click', e => {
      e.stopPropagation();
      linksWrapper.classList.contains('open') ? close() : open();
    });

    linksWrapper.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', close);
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') close();
    });

    window.addEventListener('resize', () => {
      if (window.innerWidth > 640) close();
    });
  }

  /* ── Overflow desktop (···) ─────────────────────────────── */
  _initOverflow() {
    const nav      = this.querySelector('nav');
    const moreBtn  = this.querySelector('.nav-more-btn');
    const dropdown = this.querySelector('.nav-dropdown');

    moreBtn.addEventListener('click', e => {
      e.stopPropagation();
      const isOpen = dropdown.classList.toggle('open');
      moreBtn.setAttribute('aria-expanded', String(isOpen));
    });

    document.addEventListener('click', () => {
      dropdown.classList.remove('open');
      moreBtn.setAttribute('aria-expanded', 'false');
    });

    const ro = new ResizeObserver(() => this._computeOverflow());
    ro.observe(nav);
    this._computeOverflow();
  }

  _computeOverflow() {
    if (window.innerWidth <= 640) return;

    const list     = this.querySelector('.nav-links');
    const moreBtn  = this.querySelector('.nav-more-btn');
    const dropdown = this.querySelector('.nav-dropdown');
    const wrapper  = this.querySelector('.nav-links-wrapper');

    const items = Array.from(list.querySelectorAll('li'));
    items.forEach(li => { li.style.display = ''; });
    moreBtn.classList.remove('visible');
    dropdown.innerHTML = '';

    const GAP          = 28;
    const BTN_ESTIMATE = 56;
    const wrapperWidth = wrapper.getBoundingClientRect().width;

    let usedWidth = 0;
    const overflow = [];

    items.forEach((li, i) => {
      const w      = li.getBoundingClientRect().width;
      const offset = i > 0 ? GAP : 0;
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