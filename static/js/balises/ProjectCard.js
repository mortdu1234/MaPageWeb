import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <project-card></project-card>
//
//  Attributs :
//    href        – lien de la fiche projet
//    type        – 'personnel' ou autre (académique)
//    name        – nom du projet
//    description – courte description
// ─────────────────────────────────────────────
class ProjectCard extends HTMLElement {
  connectedCallback() {
    injectCSS('project-card', 'projet.css');

    const href        = this.getAttribute('href')        || null;
    const type        = this.getAttribute('type')        || null;
    const name        = this.getAttribute('name')        || null;
    const description = this.getAttribute('description') || null;

    const isPersonal = type === 'personnel';
    const modifier   = isPersonal ? 'personal' : 'academic';

    this.innerHTML = `
      <a class="project-card project-card--${modifier}" href="${href}">
        <span class="project-badge project-badge--${modifier}">${type}</span>
        <div class="project-name">${name}</div>
        <p class="project-description">${description}</p>
        <span class="project-cta">Voir la fiche</span>
      </a>
    `;
  }
}

customElements.define('project-card', ProjectCard);