import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <project-hero-banner></project-hero-banner>
//
//  Attributs :
//    type       – type de projet
//    name       – nom du projet
//    context    – contexte (scolaire, perso…)
//    tagline    – accroche courte
//    language   – langage utilisé
//    interface  – type d'interface
//    status     – état du projet
//    gitHubPage – URL du dépôt GitHub
// ─────────────────────────────────────────────
class ProjectHeroBanner extends HTMLElement {
  connectedCallback() {
    injectCSS('project-hero-banner', 'projet.css');

    const projectType   = this.getAttribute('type')       || null;
    const name          = this.getAttribute('name')        || null;
    const context       = this.getAttribute('context')     || null;
    const tagLine       = this.getAttribute('tagline')     || null;
    const language      = this.getAttribute('language')    || null;
    const interfaceType = this.getAttribute('interface')   || null;
    const status        = this.getAttribute('status')      || null;
    const githubPage    = this.getAttribute('gitHubPage')  || null;

    let nbData = 0;
    let html = `
      <div class="project-hero">
        <return-project></return-project>
        <div class="project-hero__category">Projet ${projectType}</div>
        <h1 class="project-hero__title">${name}</h1>
    `;

    if (tagLine) html += `<p class="project-hero__tagline">${tagLine}</p>`;

    html += `<div class="project-hero__meta">`;

    const metaItem = (label, value) => {
      const divider = nbData > 0 ? `<div class="project-meta-divider"></div>` : '';
      nbData++;
      return `${divider}
        <div class="project-meta-item">
          <span class="project-meta-item__label">${label}</span>
          <span class="project-meta-item__value">${value}</span>
        </div>`;
    };

    if (language)      html += metaItem('Langage',    language);
    if (interfaceType) html += metaItem('Interface',  interfaceType);
    if (context)       html += metaItem('Contexte',   context);
    if (status)        html += metaItem('Statut',     status);

    if (githubPage) {
      if (nbData > 0) html += `<div class="project-meta-divider"></div>`;
      html += `
        <a class="project-github-link" href="${githubPage}" target="_blank" rel="noopener">
          <svg class="project-github-link__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          Voir sur GitHub
        </a>
      `;
    }

    html += `</div></div>`;
    this.innerHTML = html;
  }
}

customElements.define('project-hero-banner', ProjectHeroBanner);