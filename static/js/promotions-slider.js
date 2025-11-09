/**
 * Слайдер акційних пропозицій
 */

document.addEventListener('DOMContentLoaded', function() {
    // Ініціалізуємо обидва слайдери (мобільний і десктопний)
    initPromotionsSlider('promotionsSlider');
    initPromotionsSlider('promotionsSliderDesktop');
});

function initPromotionsSlider(sliderId) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;
    
    const container = slider.closest('.promotions-section');
    const prevBtn = container.querySelector('.promo-prev-btn');
    const nextBtn = container.querySelector('.promo-next-btn');
    
    if (!prevBtn || !nextBtn) return;
    
    let currentScroll = 0;
    
    // Функція для розрахунку ширини прокрутки (2 картки)
    function getScrollAmount() {
        const cards = slider.querySelectorAll('.product-card');
        if (cards.length === 0) return 0;
        
        const cardWidth = cards[0].offsetWidth;
        const gap = parseFloat(getComputedStyle(slider).gap) || 15;
        return (cardWidth * 2) + gap;
    }
    
    // Функція прокрутки вліво
    function scrollLeft() {
        currentScroll = Math.max(0, currentScroll - getScrollAmount());
        slider.scrollTo({
            left: currentScroll,
            behavior: 'smooth'
        });
    }
    
    // Функція прокрутки вправо
    function scrollRight() {
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        currentScroll = Math.min(maxScroll, currentScroll + getScrollAmount());
        slider.scrollTo({
            left: currentScroll,
            behavior: 'smooth'
        });
    }
    
    // Обробники кнопок навігації
    prevBtn.addEventListener('click', scrollLeft);
    nextBtn.addEventListener('click', scrollRight);
    
    // Свайп на мобільних
    let startX = 0;
    let startScrollLeft = 0;
    let isDown = false;
    
    slider.addEventListener('mousedown', (e) => {
        isDown = true;
        startX = e.pageX - slider.offsetLeft;
        startScrollLeft = slider.scrollLeft;
        slider.style.cursor = 'grabbing';
    });
    
    slider.addEventListener('mouseleave', () => {
        isDown = false;
        slider.style.cursor = 'grab';
    });
    
    slider.addEventListener('mouseup', () => {
        isDown = false;
        slider.style.cursor = 'grab';
    });
    
    slider.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - slider.offsetLeft;
        const walk = (x - startX) * 2;
        slider.scrollLeft = startScrollLeft - walk;
    });
    
    // Touch events для мобільних
    let touchStartX = 0;
    let touchScrollLeft = 0;
    
    slider.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].pageX;
        touchScrollLeft = slider.scrollLeft;
    });
    
    slider.addEventListener('touchmove', (e) => {
        const touchX = e.touches[0].pageX;
        const walk = (touchX - touchStartX) * 2;
        slider.scrollLeft = touchScrollLeft - walk;
    });
    
    // Клавіатурна навігація
    slider.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            scrollLeft();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            scrollRight();
        }
    });
    
    // Оновлення currentScroll при ручній прокрутці
    slider.addEventListener('scroll', () => {
        currentScroll = slider.scrollLeft;
        
        // Показуємо/приховуємо кнопки
        prevBtn.style.opacity = currentScroll > 0 ? '1' : '0.5';
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        nextBtn.style.opacity = currentScroll < maxScroll - 10 ? '1' : '0.5';
    });
    
    // Ініціалізація стану кнопок
    prevBtn.style.opacity = '0.5';
    
    // Оновлюємо при зміні розміру вікна
    window.addEventListener('resize', () => {
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        prevBtn.style.opacity = currentScroll > 0 ? '1' : '0.5';
        nextBtn.style.opacity = currentScroll < maxScroll - 10 ? '1' : '0.5';
    });
}

