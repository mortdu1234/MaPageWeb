// ─────────────────────────────────────────────
//  Utilitaires partagés entre les composants
// ─────────────────────────────────────────────

// Utils.js

/**
 * Injecte un <link> vers un CSS situé dans le dossier css/ voisin
 * du dossier js/ du composant appelant.
 *
 * @param {string} componentName - nom unique du composant (évite les doublons)
 * @param {string} cssFile       - nom du fichier CSS (ex: 'projets.css')
 * @param {string} moduleUrl     - toujours import.meta.url du fichier appelant
 */
export function injectCSS(componentName, cssFile, moduleUrl) {
  if (!document.querySelector(`link[data-component="${componentName}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    // js/ et css/ sont frères sous static/ -> on remonte d'un niveau puis on descend dans css/
    link.href = new URL(`../css/${cssFile}`, moduleUrl).href;
    link.dataset.component = componentName;
    document.head.appendChild(link);
  }
}