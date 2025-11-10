/**
 * Wishlist functionality
 * Управління списком бажань з AJAX та анімаціями
 */

class WishlistManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateWishlistBadges();
        this.initializeWishlistState();
    }

    async initializeWishlistState() {
        // Отримуємо поточний стан wishlist з сервера
        try {
            const response = await fetch('/wishlist/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });
            
            if (response.ok) {
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const wishlistItems = doc.querySelectorAll('.wishlist-item, .product-card[data-product-id]');
                
                // Створюємо Set з ID товарів у wishlist
                const wishlistProductIds = new Set();
                wishlistItems.forEach(item => {
                    const productId = item.dataset.productId;
                    if (productId) {
                        wishlistProductIds.add(productId);
                    }
                });
                
                // Оновлюємо стан всіх кнопок wishlist на сторінці
                this.updateButtonStates(wishlistProductIds);
            }
        } catch (error) {
            console.error('Failed to initialize wishlist state:', error);
        }
    }

    updateButtonStates(wishlistProductIds) {
        const wishlistButtons = document.querySelectorAll(
            '.btn-toggle-wishlist, .wishlist-toggle, .btn-wishlist, .wishlist-btn, .product-card__wishlist'
        );
        
        wishlistButtons.forEach(button => {
            const productId = button.dataset.productId;
            if (productId && wishlistProductIds.has(productId)) {
                button.classList.add('active');
                this.updateButtonIcon(button, true);
            } else {
                button.classList.remove('active');
                this.updateButtonIcon(button, false);
            }
        });
    }

    updateButtonIcon(button, isActive) {
        const iconElement = button.querySelector('svg, .icon-heart, .product-card__wishlist-icon');
        
        if (button.classList.contains('product-card__wishlist')) {
            const iconSpan = button.querySelector('.product-card__wishlist-icon');
            if (iconSpan) {
                iconSpan.textContent = isActive ? '♥' : '♡';
            }
        } else if (iconElement && iconElement.tagName === 'svg') {
            if (isActive) {
                iconElement.innerHTML = '<path d="M20.84 4.61C20.3292 4.099 19.7228 3.69364 19.0554 3.41708C18.3879 3.14052 17.6725 2.99817 16.95 2.99817C16.2275 2.99817 15.5121 3.14052 14.8446 3.41708C14.1772 3.69364 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.1283 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.1283 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2728 22.0329 10.6054C22.3095 9.93789 22.4518 9.22248 22.4518 8.5C22.4518 7.77752 22.3095 7.06211 22.0329 6.39464C21.7564 5.72718 21.351 5.12084 20.84 4.61Z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
            } else {
                iconElement.innerHTML = '<path d="M20.84 4.61C20.3292 4.099 19.7228 3.69364 19.0554 3.41708C18.3879 3.14052 17.6725 2.99817 16.95 2.99817C16.2275 2.99817 15.5121 3.14052 14.8446 3.41708C14.1772 3.69364 13.5708 4.099 13.06 4.61L12 5.67L10.94 4.61C9.9083 3.57831 8.50903 2.99871 7.05 2.99871C5.59096 2.99871 4.19169 3.57831 3.16 4.61C2.1283 5.64169 1.54871 7.04097 1.54871 8.5C1.54871 9.95903 2.1283 11.3583 3.16 12.39L4.22 13.45L12 21.23L19.78 13.45L20.84 12.39C21.351 11.8792 21.7564 11.2728 22.0329 10.6054C22.3095 9.93789 22.4518 9.22248 22.4518 8.5C22.4518 7.77752 22.3095 7.06211 22.0329 6.39464C21.7564 5.72718 21.351 5.12084 20.84 4.61Z" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
            }
        } else if (iconElement && iconElement.classList.contains('icon-heart')) {
            iconElement.textContent = isActive ? '♥' : '♡';
        } else if (button.classList.contains('btn-wishlist')) {
            button.textContent = isActive ? '♥' : '♡';
        }
    }

    setupEventListeners() {
        // Додавання/видалення з wishlist (toggle) - підтримка всіх варіантів селекторів
        document.addEventListener('click', (e) => {
            const wishlistBtn = e.target.closest(
                '.btn-toggle-wishlist, .wishlist-toggle, .btn-wishlist, .wishlist-btn, .product-card__wishlist'
            );
            if (wishlistBtn) {
                e.preventDefault();
                this.toggleWishlist(wishlistBtn);
            }

            // Видалення з wishlist (на сторінці wishlist)
            const removeBtn = e.target.closest('.btn-remove-wishlist');
            if (removeBtn) {
                e.preventDefault();
                this.removeFromWishlist(removeBtn);
            }

            // Додавання в кошик зі списку бажань
            const addToCartBtn = e.target.closest('.btn-add-to-cart, .product-card__add-cart');
            if (addToCartBtn && addToCartBtn.closest('.wishlist-page')) {
                e.preventDefault();
                this.addToCartFromWishlist(addToCartBtn);
            }

            // Очищення списку бажань
            const clearBtn = e.target.closest('.btn-clear-wishlist');
            if (clearBtn) {
                e.preventDefault();
                this.confirmClearWishlist(clearBtn);
            }
        });
    }

    confirmClearWishlist(button) {
        if (confirm('Ви впевнені, що хочете очистити список бажань?')) {
            window.location.href = button.href;
        }
    }

    async toggleWishlist(button) {
        const productId = button.dataset.productId;
        
        if (!productId) {
            console.error('Product ID not found');
            this.showNotification('Помилка: ID товару не знайдено', 'error');
            return;
        }
        
        const csrfToken = this.getCookie('csrftoken');
        if (!csrfToken) {
            console.error('CSRF token not found');
            this.showNotification('Помилка безпеки. Оновіть сторінку.', 'error');
            return;
        }
        
        const isInWishlist = button.classList.contains('active') || button.classList.contains('product-card__wishlist--active');
        const isWishlistPage = !!button.closest('.wishlist-page');
        button.disabled = true;

        try {
            const url = isInWishlist 
                ? `/wishlist/remove/${productId}/`
                : `/wishlist/add/${productId}/`;

            console.log('Wishlist request:', url, 'Product ID:', productId);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            console.log('Response status:', response.status);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Response data:', data);

            if (data.success) {
                if (isWishlistPage && isInWishlist) {
                    const productCard = button.closest('.product-card');
                    if (productCard) {
                        productCard.style.opacity = '0';
                        productCard.style.transform = 'scale(0.9)';
                        
                        setTimeout(() => {
                            productCard.remove();
                            
                            const remainingCards = document.querySelectorAll('.wishlist-page .product-card');
                            if (remainingCards.length === 0) {
                                location.reload();
                            }
                        }, 300);
                    }
                } else {
                    button.classList.toggle('active');
                    button.classList.toggle('product-card__wishlist--active');
                    this.updateButtonIcon(button, button.classList.contains('active') || button.classList.contains('product-card__wishlist--active'));

                    button.classList.add('animate-heart');
                    setTimeout(() => button.classList.remove('animate-heart'), 600);
                }
                
                this.updateWishlistBadges(data.count);
                this.showNotification(data.message);
            } else {
                throw new Error(data.message || 'Помилка сервера');
            }
        } catch (error) {
            console.error('Wishlist error:', error);
            this.showNotification(error.message || 'Виникла помилка. Спробуйте ще раз.', 'error');
        } finally {
            button.disabled = false;
        }
    }

    async removeFromWishlist(button) {
        const productId = button.dataset.productId;
        const wishlistItem = button.closest('.wishlist-item, .product-card');

        button.disabled = true;

        try {
            const response = await fetch(`/wishlist/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success) {
                // Анімація видалення
                wishlistItem.style.opacity = '0';
                wishlistItem.style.transform = 'translateX(-20px)';
                
                setTimeout(() => {
                    wishlistItem.remove();
                    
                    // Перевірка чи список порожній
                    const remainingItems = document.querySelectorAll('.wishlist-item, .product-card[data-product-id]');
                    if (remainingItems.length === 0) {
                        location.reload(); // Перезавантажуємо сторінку щоб показати "порожній" стан
                    }
                }, 300);

                // Оновлюємо лічильники
                this.updateWishlistBadges(data.count);

                // Показуємо повідомлення
                this.showNotification(data.message);
            }
        } catch (error) {
            console.error('Remove from wishlist error:', error);
            this.showNotification('Виникла помилка. Спробуйте ще раз.', 'error');
            button.disabled = false;
        }
    }

    async addToCartFromWishlist(button) {
        const productId = button.dataset.productId;
        
        button.disabled = true;
        const originalText = button.innerHTML;
        button.innerHTML = '<span>Додається...</span>';

        try {
            // Використовуємо існуючий cart.js функціонал
            if (window.cartManager) {
                await window.cartManager.addToCart(productId, 1);
                button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Додано';
                
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 2000);
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            button.innerHTML = originalText;
            button.disabled = false;
            this.showNotification('Виникла помилка. Спробуйте ще раз.', 'error');
        }
    }

    updateWishlistBadges(count = null) {
        // Якщо count не передано, отримуємо з DOM
        if (count === null) {
            const wishlistLinks = document.querySelectorAll('.wishlist-link');
            if (wishlistLinks.length > 0) {
                const badge = wishlistLinks[0].querySelector('.badge');
                count = badge ? parseInt(badge.textContent) : 0;
            }
        }

        // Оновлюємо всі badge елементи
        document.querySelectorAll('.wishlist-link .badge').forEach(badge => {
            if (count > 0) {
                badge.textContent = count;
                badge.classList.remove('badge-hidden');
            } else {
                badge.textContent = '';
                badge.classList.add('badge-hidden');
            }
        });

        // Оновлюємо mobile navigation badge
        document.querySelectorAll('.nav-item .nav-badge').forEach(badge => {
            if (badge.closest('.nav-item')?.href?.includes('wishlist')) {
                if (count > 0) {
                    badge.textContent = count;
                    badge.classList.remove('nav-badge-hidden');
                } else {
                    badge.textContent = '';
                    badge.classList.add('nav-badge-hidden');
                }
            }
        });
    }

    showNotification(message, type = 'success') {
        // Створюємо notification елемент
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <svg class="notification-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    ${type === 'success' 
                        ? '<path d="M20 6L9 17L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                        : '<path d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
                    }
                </svg>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Анімація появи
        setTimeout(() => notification.classList.add('show'), 10);

        // Видалення через 3 секунди
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    getCookie(name) {
        let cookieValue = null;
        
        const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (csrfInput && name === 'csrftoken') {
            return csrfInput.value;
        }
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Ініціалізація
document.addEventListener('DOMContentLoaded', () => {
    window.wishlistManager = new WishlistManager();
});

