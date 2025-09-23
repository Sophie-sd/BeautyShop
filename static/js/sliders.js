/**
 * Beauty Shop - Слайдери
 * JavaScript для горизонтальних слайдерів
 */

class HorizontalSlider {
    constructor(container) {
        this.container = container;
        this.slider = container.querySelector('.categories-slider, .products-slider');
        this.prevBtn = container.querySelector('.slider-btn-prev');
        this.nextBtn = container.querySelector('.slider-btn-next');
        
        if (!this.slider) return;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateButtons();
        
        // Touch support
        this.addTouchSupport();
        
        // Intersection Observer для lazy loading
        this.setupIntersectionObserver();
    }
    
    bindEvents() {
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.scrollPrev());
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.scrollNext());
        }
        
        // Оновлюємо кнопки при скролі
        this.slider.addEventListener('scroll', () => {
            this.updateButtons();
        });
        
        // Keyboard navigation
        this.slider.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                this.scrollPrev();
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                this.scrollNext();
            }
        });
    }
    
    scrollPrev() {
        const cardWidth = this.getCardWidth();
        const scrollAmount = cardWidth * 2; // Прокручуємо на 2 картки
        
        this.slider.scrollBy({
            left: -scrollAmount,
            behavior: 'smooth'
        });
    }
    
    scrollNext() {
        const cardWidth = this.getCardWidth();
        const scrollAmount = cardWidth * 2; // Прокручуємо на 2 картки
        
        this.slider.scrollBy({
            left: scrollAmount,
            behavior: 'smooth'
        });
    }
    
    getCardWidth() {
        const firstCard = this.slider.querySelector('.category-card, .product-card');
        if (!firstCard) return 280;
        
        const cardRect = firstCard.getBoundingClientRect();
        const gap = parseInt(getComputedStyle(this.slider).gap) || 16;
        
        return cardRect.width + gap;
    }
    
    updateButtons() {
        if (!this.prevBtn || !this.nextBtn) return;
        
        const { scrollLeft, scrollWidth, clientWidth } = this.slider;
        
        // Кнопка "назад"
        this.prevBtn.style.opacity = scrollLeft <= 0 ? '0.5' : '1';
        this.prevBtn.disabled = scrollLeft <= 0;
        
        // Кнопка "вперед"
        const isAtEnd = scrollLeft >= scrollWidth - clientWidth - 1;
        this.nextBtn.style.opacity = isAtEnd ? '0.5' : '1';
        this.nextBtn.disabled = isAtEnd;
    }
    
    addTouchSupport() {
        let isDown = false;
        let startX;
        let scrollLeftStart;
        
        this.slider.addEventListener('mousedown', (e) => {
            isDown = true;
            startX = e.pageX - this.slider.offsetLeft;
            scrollLeftStart = this.slider.scrollLeft;
            this.slider.style.cursor = 'grabbing';
        });
        
        this.slider.addEventListener('mouseleave', () => {
            isDown = false;
            this.slider.style.cursor = 'grab';
        });
        
        this.slider.addEventListener('mouseup', () => {
            isDown = false;
            this.slider.style.cursor = 'grab';
        });
        
        this.slider.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - this.slider.offsetLeft;
            const walk = (x - startX) * 2;
            this.slider.scrollLeft = scrollLeftStart - walk;
        });
        
        // Touch events для мобільних
        let touchStartX = 0;
        let touchScrollStart = 0;
        
        this.slider.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchScrollStart = this.slider.scrollLeft;
        }, { passive: true });
        
        this.slider.addEventListener('touchmove', (e) => {
            if (!touchStartX) return;
            
            const touchX = e.touches[0].clientX;
            const diff = touchStartX - touchX;
            this.slider.scrollLeft = touchScrollStart + diff;
        }, { passive: true });
        
        this.slider.addEventListener('touchend', () => {
            touchStartX = 0;
        }, { passive: true });
    }
    
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target.querySelector('img[data-src]');
                    if (img) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        observer.unobserve(entry.target);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });
        
        this.slider.querySelectorAll('.category-card, .product-card').forEach(card => {
            observer.observe(card);
        });
    }
    
    // Автоматичне прокручування (опціонально)
    startAutoScroll(interval = 5000) {
        this.autoScrollInterval = setInterval(() => {
            if (this.slider.scrollLeft >= this.slider.scrollWidth - this.slider.clientWidth - 1) {
                this.slider.scrollTo({ left: 0, behavior: 'smooth' });
            } else {
                this.scrollNext();
            }
        }, interval);
    }
    
    stopAutoScroll() {
        if (this.autoScrollInterval) {
            clearInterval(this.autoScrollInterval);
            this.autoScrollInterval = null;
        }
    }
}

// Ініціалізація слайдерів
BeautyShop.DOM.ready(() => {
    const sliderContainers = document.querySelectorAll('.categories-slider-container, .products-slider-container');
    
    sliderContainers.forEach(container => {
        new HorizontalSlider(container);
    });
    
    // Додаємо стилі курсора для слайдерів
    document.querySelectorAll('.categories-slider, .products-slider').forEach(slider => {
        slider.style.cursor = 'grab';
    });
});

// Resize handler для оновлення кнопок
window.addEventListener('resize', BeautyShop.debounce(() => {
    const sliderContainers = document.querySelectorAll('.categories-slider-container, .products-slider-container');
    sliderContainers.forEach(container => {
        const slider = new HorizontalSlider(container);
        slider.updateButtons();
    });
}, 250));

// Експорт для глобального використання
window.BeautyShop = window.BeautyShop || {};
window.BeautyShop.HorizontalSlider = HorizontalSlider;
