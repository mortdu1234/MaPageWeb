import { GameScore } from "./base.js";

// Barème cartes roses : index = nombre de cartes - 1
const BAREME_ROSE = [1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 66, 78, 91, 105, 120];

new GameScore({
  maxPlayers: 4,

  rows: [
    // ri=0 : Saison 1, eau
    { saison: "Saison 1", type: "eau",    cls: "badge-eau",    icon: "💧" },
    // ri=1 : Saison 2, eau
    { saison: "Saison 2", type: "eau",    cls: "badge-eau",    icon: "💧" },
    // ri=2 : Saison 2, herbe
    { saison: "Saison 2", type: "herbe",  cls: "badge-herbe",  icon: "🌿" },
    // ri=3 : Saison 3, eau
    { saison: "Saison 3", type: "eau",    cls: "badge-eau",    icon: "💧" },
    // ri=4 : Saison 3, herbe
    { saison: "Saison 3", type: "herbe",  cls: "badge-herbe",  icon: "🌿" },
    // ri=5 : Saison 3, pierre
    { saison: "Saison 3", type: "pierre", cls: "badge-pierre", icon: "🪨" },
    // ri=6 : Saison 3, sakura
    { saison: "Saison 3", type: "sakura", cls: "badge-sakura", icon: "🌸" },
  ],

  /**
   * Calcul du score Oanami pour un joueur donné :
   *
   * Saison 1 : bleues x3
   * Saison 2 : bleues x3 + vertes x4
   * Saison 3 : bleues x3 + vertes x4 + grises x7 + roses (barème)
   *
   * Le score total = somme des 3 manches.
   */
  computeScore(j, rows, nb, gs) {
    // Nombre de cartes par type/manche
    const eau1    = gs.getInputValue(0, j);  // Saison 1 - eau
    const eau2    = gs.getInputValue(1, j);  // Saison 2 - eau
    const herbe2  = gs.getInputValue(2, j);  // Saison 2 - herbe
    const eau3    = gs.getInputValue(3, j);  // Saison 3 - eau
    const herbe3  = gs.getInputValue(4, j);  // Saison 3 - herbe
    const pierre3 = gs.getInputValue(5, j);  // Saison 3 - pierre
    const rose3   = gs.getInputValue(6, j);  // Saison 3 - sakura

    // Saison 1 : bleues x3
    const scoreSaison1 = eau1 * 3;

    // Saison 2 : bleues x3 + vertes x4
    const scoreSaison2 = (eau2 * 3) + (herbe2 * 4);

    // Saison 3 : bleues x3 + vertes x4 + grises x7 + roses (barème)
    const nbRose       = Math.min(rose3, 15);
    const scoreRose    = nbRose > 0 ? BAREME_ROSE[nbRose - 1] : 0;
    const scoreSaison3 = (eau3 * 3) + (herbe3 * 4) + (pierre3 * 7) + scoreRose;

    return scoreSaison1 + scoreSaison2 + scoreSaison3;
  },

  buildPayload(nb, rows, players) {
    return {
      nb_joueurs: nb,
      joueurs: players,
      scores: rows.map((row, ri) => {
        const entry = { saison: row.saison, type: row.type, joueurs: {} };
        for (let j = 1; j <= nb; j++) {
          const inp = document.getElementById(`score_s${ri}_j${j}`);
          entry.joueurs[`joueur${j}`] = inp ? (parseInt(inp.value) || 0) : 0;
        }
        return entry;
      }),
    };
  },
});