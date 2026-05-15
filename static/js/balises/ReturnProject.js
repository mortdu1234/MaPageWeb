import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <return-project></return-project>
//
//  Note : styles inclus dans projet.css
// ─────────────────────────────────────────────
class ReturnProject extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <a class="project-hero__back" href="/projets">Retour aux projets</a>
    `;
  }
}

customElements.define('return-project', ReturnProject);