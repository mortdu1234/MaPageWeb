// ─────────────────────────────────────────────
//  Utilitaires partagés entre les composants
// ─────────────────────────────────────────────

// Utils.js
function getComponentsDir() {
  const scripts = document.querySelectorAll('script[src]');
  for (const script of scripts) {
    var directory = script.src;
    while (directory.substring(directory.lastIndexOf('/')+1, directory.length) != "static" ) {
      directory = directory.substring(0, directory.lastIndexOf('/'));
    }
    // en vas dans css
    return `${directory}/css`;
  }
  return '';
}

export function injectCSS(componentName, cssFile) {
  if (!document.querySelector(`link[data-component="${componentName}"]`)) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = `${getComponentsDir()}/${cssFile}`;
    link.dataset.component = componentName;
    document.head.appendChild(link);
  }
}