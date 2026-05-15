import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <site-footer></site-footer>
// ─────────────────────────────────────────────
class SiteFooter extends HTMLElement {
  connectedCallback() {
    injectCSS('site-footer', 'footer.css');
    this.innerHTML = `<footer><span class="brand">Denis ROBERT</span></footer>`;
  }
}

customElements.define('site-footer', SiteFooter);