import { injectCSS } from '/static/js/Utils.js';

class ReturnProject extends HTMLElement {
  connectedCallback() {
    injectCSS('return-project', 'projets.css', import.meta.url);
    this.innerHTML = `
      <a class="project-hero__back" href="/projets">Retour aux projets</a>
    `;
  }
}

customElements.define('return-project', ReturnProject);