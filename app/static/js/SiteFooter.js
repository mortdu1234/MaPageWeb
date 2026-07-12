import { injectCSS } from '/static/js/Utils.js';

// ─────────────────────────────────────────────
//  <site-footer></site-footer>
// ─────────────────────────────────────────────
class SiteFooter extends HTMLElement {
  connectedCallback() {
    injectCSS('site-footer', 'footer.css', import.meta.url);
    this.innerHTML = `<footer><span class="brand">Denis ROBERT</span></footer>`;
  }
}

customElements.define('site-footer', SiteFooter);