import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <game-hero-banner></game-hero-banner>
//
//  Attributs :
//    name      – nom du jeu
//    player    – nombre de joueurs
//    duree     – durée en minutes
//    age       – âge minimum
//    gamelink  – URL du site de stockage (optionnel)
// ─────────────────────────────────────────────
class GameHeroBanner extends HTMLElement {
  connectedCallback() {
    injectCSS('game-hero-banner', 'jeux.css');

    const name     = this.getAttribute('name')     || null;
    const players  = this.getAttribute('player')   || null;
    const duree    = this.getAttribute('duree')    || null;
    const age      = this.getAttribute('age')      || null;
    const gamelink = this.getAttribute('gamelink') || null;

    this.innerHTML = `
      <a class="back-btn" href="/jeux">Retour aux jeux</a>
      <h2>${name}</h2>
      <div class="game-meta">
        <strong>${players} joueurs</strong>
        <div class="project-meta-divider"></div>
        <strong>${duree} min</strong>
        <div class="project-meta-divider"></div>
        <strong>age : ${age}+</strong>
      </div>
    `;

    if (gamelink) {
      this.innerHTML += `
        <a class="game-link" href="${gamelink}" target="_blank" rel="noopener">
          Accéder au site de stockage du jeu
        </a>
      `;
    }

    this.innerHTML += '<div class="divider"></div>';
  }
}

customElements.define('game-hero-banner', GameHeroBanner);