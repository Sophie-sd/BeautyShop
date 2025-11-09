document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('recommendedSlider');
    const prevBtn = document.querySelector('.slider-prev-new');
    const nextBtn = document.querySelector('.slider-next-new');
    
    if (!slider || !prevBtn || !nextBtn) return;
    
    let currentScroll = 0;
    const scrollAmount = 300;
    
    // Функція для прокрутки вліво
    function scrollLeft() {
        currentScroll = Math.max(0, currentScroll - scrollAmount);
        slider.scrollTo({
            left: currentScroll,
            behavior: 'smooth'
        });
    }
    
    // Функція для прокрутки вправо
    function scrollRight() {
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        currentScroll = Math.min(maxScroll, currentScroll + scrollAmount);
        slider.scrollTo({
            left: currentScroll,
            behavior: 'smooth'
        });
    }
    
    // Обробники подій для кнопок
    prevBtn.addEventListener('click', scrollLeft);
    nextBtn.addEventListener('click', scrollRight);
    
    // Оновлення currentScroll при ручній прокрутці
    slider.addEventListener('scroll', () => {
        currentScroll = slider.scrollLeft;
        
        // Показуємо/приховуємо кнопки
        prevBtn.style.opacity = currentScroll > 0 ? '1' : '0.5';
        const maxScroll = slider.scrollWidth - slider.clientWidth;
        nextBtn.style.opacity = currentScroll < maxScroll - 10 ? '1' : '0.5';
    });
    
    // Touch swipe для мобільних пристроїв
    let touchStartX = 0;
    let touchEndX = 0;
    let isDragging = false;
    
    slider.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        isDragging = true;
    });
    
    slider.addEventListener('touchmove', (e) => {
        if (!isDragging) return;
        touchEndX = e.touches[0].clientX;
    });
    
    slider.addEventListener('touchend', () => {
        if (!isDragging) return;
        const swipeThreshold = 50;
        
        if (touchEndX < touchStartX - swipeThreshold) {
            scrollRight();
        } else if (touchEndX > touchStartX + swipeThreshold) {
            scrollLeft();
        }
        
        isDragging = false;
    });
    
    // Підтримка клавіатури
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            scrollLeft();
        } else if (e.key === 'ArrowRight') {
            scrollRight();
        }
    });
    
    // Ініціалізація стану кнопок
    prevBtn.style.opacity = '0.5';
});

