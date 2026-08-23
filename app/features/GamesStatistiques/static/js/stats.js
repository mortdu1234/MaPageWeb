/**
 * stats.js
 * Charge et affiche les statistiques (vue d'ensemble, classement général,
 * détail par jeu avec historique des parties, détail par joueur avec
 * historique dépliable par jeu) via l'API JSON du blueprint `statistiques`.
 */

const API_BASE = "/statistiques/api";

// Cache des historiques de parties déjà chargés : "joueurId-jeuId" -> data
const cacheJoueurJeu = new Map();

document.addEventListener("DOMContentLoaded", () => {
  chargerVueEnsemble();

  const selectJeu = document.getElementById("select-jeu");
  selectJeu.addEventListener("change", () => {
    const jeuId = selectJeu.value;
    if (jeuId) {
      chargerStatsJeu(jeuId);
    } else {
      resetSectionJeu();
    }
  });

  const selectJoueur = document.getElementById("select-joueur");
  selectJoueur.addEventListener("change", () => {
    const joueurId = selectJoueur.value;
    if (joueurId) {
      chargerStatsJoueur(joueurId);
    } else {
      resetSectionJoueur();
    }
  });

  document.getElementById("toggle-jeu-parties").addEventListener("click", (e) => {
    const list = document.getElementById("jeu-parties-list");
    const btn = e.currentTarget;
    const ouvert = !list.hidden;
    list.hidden = ouvert;
    btn.setAttribute("aria-expanded", String(!ouvert));
    btn.textContent = ouvert ? "Afficher l'historique des parties" : "Masquer l'historique des parties";
  });

  // Délégation d'événements : un clic sur une ligne "jeu" du tableau joueur
  // déplie/replie l'historique des parties de ce joueur pour ce jeu.
  document.getElementById("stats-joueur-body").addEventListener("click", (e) => {
    const row = e.target.closest("tr.joueur-jeu-row");
    if (row) toggleDetailJoueurJeu(row);
  });
});

function resetSectionJeu() {
  document.getElementById("jeu-extremes").hidden = true;
  document.getElementById("table-jeu").hidden = true;
  document.getElementById("jeu-empty").hidden = true;
  document.getElementById("jeu-parties-wrap").hidden = true;
  document.getElementById("jeu-parties-list").hidden = true;
  document.getElementById("jeu-parties-list").innerHTML = "";
  const btn = document.getElementById("toggle-jeu-parties");
  btn.textContent = "Afficher l'historique des parties";
  btn.setAttribute("aria-expanded", "false");
}

function resetSectionJoueur() {
  document.getElementById("joueur-totaux").hidden = true;
  document.getElementById("table-joueur").hidden = true;
  document.getElementById("joueur-empty").hidden = true;
  document.getElementById("joueur-hint").hidden = true;
}

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
  const extremesContainer = document.getElementById("jeu-extremes");
  const table = document.getElementById("table-jeu");
  const empty = document.getElementById("jeu-empty");
  const tbody = document.getElementById("classement-jeu-body");
  const partiesWrap = document.getElementById("jeu-parties-wrap");
  const partiesList = document.getElementById("jeu-parties-list");
  const toggleBtn = document.getElementById("toggle-jeu-parties");

  // On replie l'historique à chaque changement de jeu.
  partiesList.hidden = true;
  partiesList.innerHTML = "";
  toggleBtn.textContent = "Afficher l'historique des parties";
  toggleBtn.setAttribute("aria-expanded", "false");

  try {
    const res = await fetch(`${API_BASE}/jeu/${jeuId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    afficherExtremesJeu(data.extremes);

    if (!data.classement || data.classement.length === 0) {
      table.hidden = true;
      empty.hidden = false;
      partiesWrap.hidden = true;
      return;
    }

    tbody.innerHTML = data.classement
      .map(
        (j) => `
        <tr>
          <td class="td-left">${j.prenom} ${j.nom}</td>
          <td>${j.nb_parties}</td>
          <td><span class="stats-badge gold">${j.nb_premiere}</span></td>
          <td>${j.nb_derniere}</td>
          <td>${j.score_moyen ?? "—"}</td>
          <td>${j.score_min ?? "—"}</td>
          <td>${j.score_max ?? "—"}</td>
        </tr>`
      )
      .join("");

    empty.hidden = true;
    table.hidden = false;

    partiesList.innerHTML = renderPartiesList(data.parties);
    partiesWrap.hidden = false;
  } catch (err) {
    console.error("Erreur lors du chargement des statistiques du jeu :", err);
    extremesContainer.hidden = true;
    table.hidden = true;
    empty.hidden = false;
    empty.textContent = "Impossible de charger les statistiques pour ce jeu.";
    partiesWrap.hidden = true;
  }
}

function afficherExtremesJeu(extremes) {
  const container = document.getElementById("jeu-extremes");
  if (!extremes || (!extremes.score_plus_bas && !extremes.score_plus_haut)) {
    container.hidden = true;
    container.innerHTML = "";
    return;
  }

  const bas = extremes.score_plus_bas;
  const haut = extremes.score_plus_haut;

  container.innerHTML = `
    ${bas ? `
      <div class="stats-card">
        <span class="stats-card-value">${bas.score}</span>
        <span class="stats-card-label">Score le plus bas — ${bas.prenom} ${bas.nom}</span>
      </div>` : ""}
    ${haut ? `
      <div class="stats-card">
        <span class="stats-card-value">${haut.score}</span>
        <span class="stats-card-label">Score le plus haut — ${haut.prenom} ${haut.nom}</span>
      </div>` : ""}
  `;
  container.hidden = false;
}

// ─── Statistiques par joueur ──────────────────────────────────────────────

async function chargerStatsJoueur(joueurId) {
  const totauxContainer = document.getElementById("joueur-totaux");
  const table = document.getElementById("table-joueur");
  const empty = document.getElementById("joueur-empty");
  const hint = document.getElementById("joueur-hint");
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
      hint.hidden = true;
      return;
    }

    tbody.innerHTML = data.par_jeu
      .map(
        (j) => `
        <tr class="joueur-jeu-row" data-joueur-id="${data.id}" data-jeu-id="${j.jeu_id}" tabindex="0" role="button" aria-expanded="false">
          <td class="td-left">▸ ${capitalize(j.jeu)}</td>
          <td>${j.nb_parties}</td>
          <td><span class="stats-badge gold">${j.nb_premiere}</span></td>
          <td>${j.nb_derniere}</td>
          <td>${j.score_moyen ?? "—"}</td>
          <td>${j.score_min ?? "—"}</td>
          <td>${j.score_max ?? "—"}</td>
        </tr>`
      )
      .join("");

    empty.hidden = true;
    table.hidden = false;
    hint.hidden = false;
  } catch (err) {
    console.error("Erreur lors du chargement des statistiques du joueur :", err);
    totauxContainer.hidden = true;
    table.hidden = true;
    empty.hidden = false;
    empty.textContent = "Impossible de charger les statistiques pour ce joueur.";
    hint.hidden = true;
  }
}

async function toggleDetailJoueurJeu(row) {
  const joueurId = row.dataset.joueurId;
  const jeuId = row.dataset.jeuId;
  const next = row.nextElementSibling;

  // Si la ligne de détail existe déjà juste en dessous, on replie/déplie simplement.
  if (next && next.classList.contains("joueur-jeu-detail-row")) {
    const masque = next.hidden;
    next.hidden = !masque;
    row.setAttribute("aria-expanded", String(masque));
    row.querySelector("td.td-left").textContent =
      (masque ? "▾ " : "▸ ") + row.querySelector("td.td-left").textContent.slice(2);
    return;
  }

  // Sinon on crée la ligne de détail et on charge les données (avec cache).
  const detailRow = document.createElement("tr");
  detailRow.className = "joueur-jeu-detail-row";
  const nbCols = row.children.length;
  detailRow.innerHTML = `<td colspan="${nbCols}"><div class="parties-list stats-loading">Chargement…</div></td>`;
  row.insertAdjacentElement("afterend", detailRow);
  row.setAttribute("aria-expanded", "true");
  row.querySelector("td.td-left").textContent =
    "▾ " + row.querySelector("td.td-left").textContent.slice(2);

  const cacheKey = `${joueurId}-${jeuId}`;
  try {
    let parties = cacheJoueurJeu.get(cacheKey);
    if (!parties) {
      const res = await fetch(`${API_BASE}/joueur/${joueurId}/jeu/${jeuId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      parties = await res.json();
      cacheJoueurJeu.set(cacheKey, parties);
    }
    detailRow.querySelector("td").innerHTML = renderPartiesList(parties);
  } catch (err) {
    console.error("Erreur lors du chargement du détail des parties :", err);
    detailRow.querySelector("td").innerHTML =
      '<p class="stats-empty">Impossible de charger le détail des parties.</p>';
  }
}

// ─── Rendu commun : liste de parties avec le score de chaque joueur ───────

function renderPartiesList(parties) {
  if (!parties || parties.length === 0) {
    return '<p class="stats-empty">Aucune partie enregistrée.</p>';
  }

  return parties
    .map(
      (p) => `
      <div class="partie-card">
        <div class="partie-card-header">Partie n°${p.partie_id}</div>
        <ul class="partie-scores">
          ${p.scores
            .map(
              (s) => `
            <li class="${s.gagnant ? "is-winner" : ""}">
              <span>${s.prenom} ${s.nom}${s.gagnant ? ' <span class="stats-badge gold">★</span>' : ""}</span>
              <strong>${s.score}</strong>
            </li>`
            )
            .join("")}
        </ul>
      </div>`
    )
    .join("");
}

// ─── Utils ─────────────────────────────────────────────────────────────────

function capitalize(str) {
  if (!str) return "";
  return str.charAt(0).toUpperCase() + str.slice(1);
}