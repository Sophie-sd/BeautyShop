class MarqueeController {
    constructor() {
        this.phrases = [
            'Знижки для оптових клієнтів 🎯',
            'Швидка доставка по Україні 🚚',
            'Новинки та хіти для салонів щотижня ✨',
            'Повернення та обмін — легко й швидко 🔄',
            'Бонуси для постійних клієнтів 🎁'
        ];
        this.currentIndex = 0;
        this.interval = 4000;
        this.init();
    }

    init() {
        const containers = document.querySelectorAll('.marquee-container');
        
        containers.forEach(container => {
            const textElement = container.querySelector('.marquee-text');
            if (textElement) {
                this.updateText(textElement);
                this.startRotation(textElement);
            }
        });
    }

    updateText(element) {
        element.textContent = this.phrases[this.currentIndex];
    }

    startRotation(element) {
        setInterval(() => {
            this.currentIndex = (this.currentIndex + 1) % this.phrases.length;
            element.style.animation = 'none';
            element.offsetHeight;
            element.style.animation = 'fadeInOut 4s ease-in-out';
            this.updateText(element);
        }, this.interval);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.marquee-container')) {
        window.marqueeController = new MarqueeController();
    }
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarqueeController;
}
