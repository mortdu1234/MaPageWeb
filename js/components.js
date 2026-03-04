// ─────────────────────────────────────────────
//  <nav-bar></nav-bar>
//  Attribut "root" : chemin vers la racine du site
//  ex: <nav-bar root="./"></nav-bar>        (pages racine)
//      <nav-bar root="../"></nav-bar>       (pages dans sous-dossiers)
// ─────────────────────────────────────────────
class NavBar extends HTMLElement {
  connectedCallback() {
    const root = this.getAttribute('root') || './';

    this.innerHTML = `
      <nav>
        <a class="nav-brand" href="${root}index.html">Denis ROBERT</a>
        <ul class="nav-links">
          <li><a href="${root}index.html">Accueil</a></li>
          <li><a href="${root}jeux.html">Jeux de société</a></li>
          <li><a href="${root}apropos.html">À propos</a></li>
          <li><a href="${root}contact.html">Contact</a></li>
          <li><a href="${root}mesprojets.html">Mes projets</a></li>
        </ul>
      </nav>
    `;

    // Lien actif : compare l'URL courante avec chaque lien
    const currentFile = window.location.pathname.split('/').pop() || 'index.html';
    this.querySelectorAll('.nav-links a').forEach(link => {
      const linkFile = link.getAttribute('href').split('/').pop();
      if (linkFile === currentFile) link.classList.add('active');
    });
  }
}

class ProjectHeroBanner extends HTMLElement {
  connectedCallback() {
    const projectType = this.getAttribute("type") || null
    const name = this.getAttribute("name") || null;
    const context = this.getAttribute("context") || null;
    const tagLine = this.getAttribute("tagline") || null;
    const language = this.getAttribute("language") || null;
    const interfaceType = this.getAttribute("interface") || null;
    const status = this.getAttribute("status") || null;
    const githubPage = this.getAttribute("gitHubPage") || null

    let nbData = 0;
    let html = `
      <div class="project-hero">
        <return-project></return-project>
        <div class="project-hero__category">Projet ${projectType}</div>
        <h1 class="project-hero__title">${name}</h1>
    `
    if (tagLine != null) {html += `<p class="project-hero__tagline">${tagLine}</p>`}
    
    // #######################################################
    // GESTION DES META DATA
    // #######################################################
    html += `<div class="project-hero__meta">`

    if (language != null) {
      if (nbData > 0) {html += `<div class="project-meta-divider"></div>`}
      html += `
        <div class="project-meta-item">
          <span class="project-meta-item__label">Langage</span>
          <span class="project-meta-item__value">${language}</span>
        </div>
      `
      nbData += 1;
    }

    if (interfaceType != null) {
      if (nbData > 0) {html += `<div class="project-meta-divider"></div>`}
      html += `
        <div class="project-meta-item">
            <span class="project-meta-item__label">Interface</span>
            <span class="project-meta-item__value">${interfaceType}</span>
        </div>
      `
      nbData += 1;
    }

    if (context != null) {
      if (nbData > 0) {html += `<div class="project-meta-divider"></div>`}
      html += `
        <div class="project-meta-item">
            <span class="project-meta-item__label">Contexte</span>
            <span class="project-meta-item__value">${context}</span>
        </div>
      `
      nbData += 1;
    }


    if (status != null) {
      if (nbData > 0) {html += `<div class="project-meta-divider"></div>`}
      html += `
        <div class="project-meta-item">
          <span class="project-meta-item__label">Statut</span>
          <span class="project-meta-item__value">${status}</span>
        </div>
      `
      nbData += 1;
    }

    if (githubPage != null) {
      if (nbData > 0) {html += `<div class="project-meta-divider"></div>`}
      html += `
        <a class="project-github-link" href="${githubPage}" target="_blank" rel="noopener">
          <svg class="project-github-link__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
          </svg>
          Voir sur GitHub
        </a>
      `
    }

    html += `
        </div>
      </div>
    `

    this.innerHTML = html;
  }
}

// ─────────────────────────────────────────────
//  <site-footer></site-footer>
// ─────────────────────────────────────────────
class SiteFooter extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <footer>
        <span class="brand">Denis ROBERT</span>
      </footer>
    `;
  }
}


// ─────────────────────────────────────────────
//  <return-project></return-project>
// ─────────────────────────────────────────────
 class ReturnProject extends HTMLElement {
  connectedCallback() {
    this.innerHTML = `
      <a class="project-hero__back" href="../mesprojets.html">Retour aux projets</a>
    `;
  } 
 }

// Enregistrement des composants
customElements.define('nav-bar', NavBar);
customElements.define('site-footer', SiteFooter);
customElements.define('return-project', ReturnProject);
customElements.define('project-hero-banner', ProjectHeroBanner);

// ─────────────────────────────────────────────
//  Formulaire de contact (utilisé sur contact.html)
// ─────────────────────────────────────────────
function handleSubmit(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  btn.textContent = 'Message envoyé ✓';
  btn.style.background = '#5a7a4a';
  btn.disabled = true;
  e.target.reset();
  setTimeout(() => {
    btn.textContent = 'Envoyer le message';
    btn.style.background = '';
    btn.disabled = false;
  }, 4000);
}
