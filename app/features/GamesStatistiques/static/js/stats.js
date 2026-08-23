/**
 * stats.js
 * Charge et affiche les statistiques (vue d'ensemble, classement général,
 * détail par jeu, détail par joueur) via l'API JSON du blueprint
 * `statistiques` (voir routes.py).
 */

const API_BASE = "/statistiques/api";

document.addEventListener("DOMContentLoaded", () => {
  chargerVueEnsemble();

  const selectJeu = document.getElementById("select-jeu");
  selectJeu.addEventListener("change", () => {
    const jeuId = selectJeu.value;
    if (jeuId) {
      chargerStatsJeu(jeuId);
    } else {
      document.getElementById("table-jeu").hidden = true;
      document.getElementById("jeu-empty").hidden = true;
    }
  });

  const selectJoueur = document.getElementById("select-joueur");
  selectJoueur.addEventListener("change", () => {
    const joueurId = selectJoueur.value;
    if (joueurId) {
      chargerStatsJoueur(joueurId);
    } else {
      document.getElementById("table-joueur").hidden = true;
      document.getElementById("joueur-empty").hidden = true;
      document.getElementById("joueur-totaux").hidden = true;
    }
  });
});

// ─── Vue d'ensemble + classement général ──────────────────────────────────

async function chargerVueEnsemble() {
  try {
    const res = await fetch(`${API_BASE}/global`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    afficherPartiesParJeu(data.parties_par_jeu);
    afficherClassementGlobal(data.classement);
  } catch (err) {
    console.error("Erreur lors du chargement des statistiques globales :", err);
    document.getElementById("parties-par-jeu").innerHTML =
      '<p class="stats-empty">Impossible de charger les statistiques.</p>';
    document.getElementById("classement-global-body").innerHTML =
      '<tr><td colspan="4" class="stats-empty">Impossible de charger les statistiques.</td></tr>';
  }
}

function afficherPartiesParJeu(liste) {
  const container = document.getElementById("parties-par-jeu");
  if (!liste || liste.length === 0) {
    container.innerHTML = '<p class="stats-empty">Aucun jeu enregistré.</p>';
    return;
  }
  container.innerHTML = liste
    .map(
      (jeu) => `
      <div class="stats-card is-gold">
        <span class="stats-card-value">${jeu.nb_parties}</span>
        <span class="stats-card-label">${capitalize(jeu.name)}</span>
      </div>`
    )
    .join("");
}

function afficherClassementGlobal(liste) {
  const tbody = document.getElementById("classement-global-body");
  const joueurs = (liste || []).filter((j) => j.nb_parties > 0);

  if (joueurs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="stats-empty">Aucune partie complète enregistrée pour le moment.</td></tr>';
    return;
  }

  tbody.innerHTML = joueurs
    .map(
      (j) => `
      <tr>
        <td class="td-left">${j.prenom} ${j.nom}</td>
        <td>${j.nb_parties}</td>
        <td><span class="stats-badge gold">${j.nb_premiere}</span></td>
        <td>${j.nb_derniere}</td>
      </tr>`
    )
    .join("");
}

// ─── Statistiques par jeu ─────────────────────────────────────────────────

async function chargerStatsJeu(jeuId) {
  const table = document.getElementById("table-jeu");
  const empty = document.getElementById("jeu-empty");
  const tbody = document.getElementById("classement-jeu-body");

  try {
    const res = await fetch(`${API_BASE}/jeu/${jeuId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const liste = await res.json();

    if (!liste || liste.length === 0) {
      table.hidden = true;
      empty.hidden = false;
      return;
    }

    tbody.innerHTML = liste
      .map(
        (j) => `
        <tr>
          <td class="td-left">${j.prenom} ${j.nom}</td>
          <td>${j.nb_parties}</td>
          <td><span class="stats-badge gold">${j.nb_premiere}</span></td>
          <td>${j.nb_derniere}</td>
          <td>${j.score_moyen ?? "—"}</td>
        </tr>`
      )
      .join("");

    empty.hidden = true;
    table.hidden = false;
  } catch (err) {
    console.error("Erreur lors du chargement des statistiques du jeu :", err);
    table.hidden = true;
    empty.hidden = false;
    empty.textContent = "Impossible de charger les statistiques pour ce jeu.";
  }
}

// ─── Statistiques par joueur ──────────────────────────────────────────────

async function chargerStatsJoueur(joueurId) {
  const totauxContainer = document.getElementById("joueur-totaux");
  const table = document.getElementById("table-joueur");
  const empty = document.getElementById("joueur-empty");
  const tbody = document.getElementById("stats-joueur-body");

  try {
    const res = await fetch(`${API_BASE}/joueur/${joueurId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    totauxContainer.innerHTML = `
      <div class="stats-card">
        <span class="stats-card-value">${data.nb_parties_total}</span>
        <span class="stats-card-label">Parties jouées</span>
      </div>
      <div class="stats-card is-gold">
        <span class="stats-card-value">${data.nb_premiere_total}</span>
        <span class="stats-card-label">1<sup>ère</sup> place</span>
      </div>
      <div class="stats-card">
        <span class="stats-card-value">${data.nb_derniere_total}</span>
        <span class="stats-card-label">Dernière place</span>
      </div>
    `;
    totauxContainer.hidden = false;

    if (!data.par_jeu || data.par_jeu.length === 0) {
      table.hidden = true;
      empty.hidden = false;
      return;
    }

    tbody.innerHTML = data.par_jeu
      .map(
        (j) => `
        <tr>
          <td class="td-left">${capitalize(j.jeu)}</td>
          <td>${j.nb_parties}</td>
          <td><span class="stats-badge gold">${j.nb_premiere}</span></td>
          <td>${j.nb_derniere}</td>
          <td>${j.score_moyen ?? "—"}</td>
        </tr>`
      )
      .join("");

    empty.hidden = true;
    table.hidden = false;
  } catch (err) {
    console.error("Erreur lors du chargement des statistiques du joueur :", err);
    totauxContainer.hidden = true;
    table.hidden = true;
    empty.hidden = false;
    empty.textContent = "Impossible de charger les statistiques pour ce joueur.";
  }
}

// ─── Utils ─────────────────────────────────────────────────────────────────

function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}