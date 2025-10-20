/**
 * Common Event Handlers
 * Загальні обробники подій для сайту Beauty Shop
 */

(function() {
    'use strict';

    // Filters toggle functionality
    function initFiltersToggle() {
        const toggleBtn = document.getElementById('filtersToggleBtn');
        const dropdown = document.getElementById('filtersDropdown');
        const countSpan = document.getElementById('filtersCount');
        
        if (!toggleBtn || !dropdown) return;
        
        toggleBtn.addEventListener('click', function() {
            const isExpanded = this.getAttribute('aria-expanded') === 'true';
            
            if (isExpanded) {
                // Закриваємо
                dropdown.classList.add('hidden');
                this.setAttribute('aria-expanded', 'false');
            } else {
                // Відкриваємо
                dropdown.classList.remove('hidden');
                this.setAttribute('aria-expanded', 'true');
            }
        });
        
        // Закриття при кліку поза фільтрами
        document.addEventListener('click', function(e) {
            if (!toggleBtn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.add('hidden');
                toggleBtn.setAttribute('aria-expanded', 'false');
            }
        });
        
        // Оновлення лічильника активних фільтрів
        function updateFiltersCount() {
            const activeFilters = dropdown.querySelectorAll('.filter-select, .price-range__input');
            let count = 0;
            
            activeFilters.forEach(filter => {
                if (filter.value && filter.value.trim() !== '') {
                    count++;
                }
            });
            
            if (count > 0) {
                countSpan.textContent = `(${count})`;
                countSpan.classList.remove('hidden');
            } else {
                countSpan.classList.add('hidden');
            }
        }
        
        // Слухаємо зміни у фільтрах
        dropdown.addEventListener('change', updateFiltersCount);
        dropdown.addEventListener('input', updateFiltersCount);
    }

    // Accordion toggles (для мобільного футера)
    function initAccordions() {
        const accordionToggles = document.querySelectorAll('[data-accordion-toggle]');
        
        accordionToggles.forEach(button => {
            button.addEventListener('click', function() {
                const item = this.parentElement;
                const content = item.querySelector('.accordion-content');
                
                // Закриваємо всі інші акордеони
                document.querySelectorAll('.accordion-item').forEach(otherItem => {
                    if (otherItem !== item && otherItem.classList.contains('active')) {
                        otherItem.classList.remove('active');
                        const otherContent = otherItem.querySelector('.accordion-content');
                        if (otherContent) {
                            otherContent.style.maxHeight = null;
                        }
                    }
                });
                
                // Перемикаємо поточний акордеон
                item.classList.toggle('active');
                
                if (item.classList.contains('active')) {
                    content.style.maxHeight = content.scrollHeight + 'px';
                } else {
                    content.style.maxHeight = null;
                }
            });
        });
    }

    // Filter actions
    function initFilterActions() {
        const clearBtn = document.getElementById('clearFilters');
        const applyBtn = document.getElementById('applyFilters');
        
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                // Очистити всі фільтри
                const filters = document.querySelectorAll('.filter-select, .price-range__input');
                filters.forEach(filter => {
                    filter.value = '';
                });
                
                // Очистити активні чіпи
                const activeFiltersContainer = document.getElementById('activeFilters');
                if (activeFiltersContainer) {
                    activeFiltersContainer.innerHTML = '';
                    activeFiltersContainer.classList.add('hidden');
                }
                
                // Оновити лічильник
                const countSpan = document.getElementById('filtersCount');
                if (countSpan) {
                    countSpan.classList.add('hidden');
                }
            });
        }
        
        if (applyBtn) {
            applyBtn.addEventListener('click', function() {
                // Застосувати фільтри - тут можна додати логіку фільтрації
                
                // Закрити dropdown після застосування
                const dropdown = document.getElementById('filtersDropdown');
                const toggleBtn = document.getElementById('filtersToggleBtn');
                
                if (dropdown && toggleBtn) {
                    dropdown.classList.add('hidden');
                    toggleBtn.setAttribute('aria-expanded', 'false');
                }
            });
        }
    }

    // Cancel order handler
    function initCancelOrderButtons() {
        const cancelButtons = document.querySelectorAll('[data-cancel-order]');
        
        cancelButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const orderId = this.getAttribute('data-cancel-order');
                
                if (confirm('Ви впевнені, що хочете скасувати це замовлення?')) {
                    // AJAX запит на скасування
                    if (window.BeautyShop && window.BeautyShop.Ajax) {
                        window.BeautyShop.Ajax.post('/orders/cancel/', { order_id: orderId })
                            .then(response => {
                                if (response.success) {
                                    location.reload();
                                } else {
                                    alert(response.error || 'Помилка скасування замовлення');
                                }
                            })
                            .catch(error => {
                                console.error('Cancel order error:', error);
                                alert('Помилка скасування замовлення');
                            });
                    }
                }
            });
        });
    }

    // Confirm links (для підтвердження дій)
    function initConfirmLinks() {
        const confirmLinks = document.querySelectorAll('[data-confirm]');
        
        confirmLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                const message = this.getAttribute('data-confirm');
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    }

    // Alert close buttons
    function initAlertCloseButtons() {
        const closeButtons = document.querySelectorAll('.alert-close');
        
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                const alert = this.closest('.alert');
                if (alert && window.BeautyShop && window.BeautyShop.Animations) {
                    window.BeautyShop.Animations.fadeOut(alert, 200);
                } else if (alert) {
                    alert.style.display = 'none';
                }
            });
        });
    }

    // Ініціалізація при завантаженні DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            initFiltersToggle();
            initFilterActions();
            initAccordions();
            initCancelOrderButtons();
            initConfirmLinks();
            initAlertCloseButtons();
        });
    } else {
        initFiltersToggle();
        initFilterActions();
        initAccordions();
        initCancelOrderButtons();
        initConfirmLinks();
        initAlertCloseButtons();
    }
})();

