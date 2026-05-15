import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <game-card></game-card>
//
//  Attributs :
//    href        – lien de la fiche jeu
//    name        – nom du jeu
//    description – courte description
// ─────────────────────────────────────────────
class GameCard extends HTMLElement {
  connectedCallback() {
    injectCSS('game-card', 'jeux.css');

    const href        = this.getAttribute('href')        || null;
    const name        = this.getAttribute('name')        || null;
    const description = this.getAttribute('description') || 'Description du jeu';

    this.innerHTML = `
      <a class="game-card" href="${href}">
        <div class="game-title">${name}</div>
        <p class="game-desc">${description}</p>
        <span class="game-link">Voir la fiche</span>
      </a>
    `;
  }
}

customElements.define('game-card', GameCard);