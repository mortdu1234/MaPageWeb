import { injectCSS } from './Utils.js';

// ─────────────────────────────────────────────
//  <images-carousel src1="..." alt1="..." src2="..." alt2="...">
//  </images-carousel>
// ─────────────────────────────────────────────
class ImagesCarousel extends HTMLElement {
  connectedCallback() {
    console.log('Connected carousel with attributes:', this.attributes);
    injectCSS('images-carousel', 'projet.css');
    const slides = this.getSlides();
    this.render(slides);
    this.initCarousel();
  }

  // Récupère tous les srcX et altX dans l'ordre
  getSlides() {
    const slides = [];

    for (const attr of this.attributes) {
      const match = attr.name.match(/^src(\d+)$/);
      if (match) {
        const index = parseInt(match[1]);
        if (!slides[index - 1]) slides[index - 1] = {};
        slides[index - 1].src = attr.value;
      }

      const matchAlt = attr.name.match(/^alt(\d+)$/);
      if (matchAlt) {
        const index = parseInt(matchAlt[1]);
        if (!slides[index - 1]) slides[index - 1] = {};
        slides[index - 1].alt = attr.value;
      }
    }

    return slides.filter(Boolean);
  }

  render(slides) {
    this.innerHTML = `
      <div class="project-carousel">
        <button class="project-carousel__btn project-carousel__btn--prev" aria-label="Image précédente">&#8592;</button>
        <div class="project-carousel__track-wrapper">
          <div class="project-carousel__track">
            ${slides.map(slide => `
              <div class="project-carousel__slide">
                <img src="${slide.src}" alt="${slide.alt ?? ''}">
              </div>
            `).join('')}
          </div>
        </div>
        <button class="project-carousel__btn project-carousel__btn--next" aria-label="Image suivante">&#8594;</button>
        <div class="project-carousel__dots"></div>
      </div>
    `;
  }

  initCarousel() {
    const track = this.querySelector('.project-carousel__track');
    const dotsContainer = this.querySelector('.project-carousel__dots');
    const slides = this.querySelectorAll('.project-carousel__slide');
    const prevBtn = this.querySelector('.project-carousel__btn--prev');
    const nextBtn = this.querySelector('.project-carousel__btn--next');

    let current = 0;

    // Création des dots
    slides.forEach((_, i) => {
      const dot = document.createElement('button');
      dot.classList.add('project-carousel__dot');
      if (i === 0) dot.classList.add('project-carousel__dot--active');
      dot.addEventListener('click', () => goTo(i));
      dotsContainer.appendChild(dot);
    });

    const dots = () => dotsContainer.querySelectorAll('.project-carousel__dot');

    const goTo = (index) => {
      current = (index + slides.length) % slides.length; // boucle infinie
      track.style.transform = `translateX(-${current * 100}%)`;
      dots().forEach((d, i) => d.classList.toggle('project-carousel__dot--active', i === current));
    };

    prevBtn.addEventListener('click', () => goTo(current - 1));
    nextBtn.addEventListener('click', () => goTo(current + 1));
  }
}

customElements.define('images-carousel', ImagesCarousel);