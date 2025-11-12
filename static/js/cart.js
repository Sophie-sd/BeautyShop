class ShoppingCart {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateCartDisplay();
    }

    bindEvents() {
        document.addEventListener('click', (e) => {
            const addBtn = e.target.closest('.add-to-cart, .add-to-cart-btn, .product-card__add-cart, .btn-add-cart');
            if (addBtn) {
                e.preventDefault();
                this.handleAddToCart(addBtn);
            }
        });

        document.addEventListener('click', (e) => {
            const removeBtn = e.target.closest('.cart-item__remove, .remove-from-cart, .btn-remove-from-cart');
            if (removeBtn) {
                e.preventDefault();
                this.handleRemoveFromCart(removeBtn);
            }
        });

        document.addEventListener('click', (e) => {
            const quantityBtn = e.target.closest('.quantity-btn');
            if (quantityBtn) {
                e.preventDefault();
                this.handleQuantityButton(quantityBtn);
            }
        });

        document.addEventListener('change', (e) => {
            if (e.target.matches('.cart-quantity')) {
                this.handleQuantityChange(e.target);
            }
        });

        document.addEventListener('click', (e) => {
            const clearBtn = e.target.closest('.clear-cart, .btn-clear-cart');
            if (clearBtn) {
                e.preventDefault();
                this.handleClearCart();
            }
        });

        document.addEventListener('click', (e) => {
            const promoBtn = e.target.closest('.apply-promo-btn');
            if (promoBtn) {
                e.preventDefault();
                this.handleApplyPromo();
            }
        });
    }

    async handleAddToCart(button) {
        const productId = button.dataset.productId;
        const productName = button.dataset.productName || 'Товар';
        const quantity = this.getQuantityFromForm(button) || 1;

        if (!productId) {
            console.error('Product ID is missing');
            return;
        }

        const csrfToken = this.getCsrfToken();
        if (!csrfToken) {
            this.showErrorMessage('Помилка безпеки. Оновіть сторінку.');
            return;
        }

        this.setButtonLoading(button, true);

        try {
            const formData = new FormData();
            formData.append('quantity', quantity);

            const response = await fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: formData,
                credentials: 'same-origin',
            });

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error:', response.status, errorText);
                throw new Error(`Помилка сервера: ${response.status}`);
            }

            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                console.error('JSON parse error:', jsonError);
                throw new Error('Помилка обробки відповіді сервера');
            }

            if (data.success) {
                this.showSuccessMessage('Товар додано до кошика');
                this.updateCartDisplay(data.cart);
                this.animateCartIcon();
            } else {
                this.showErrorMessage(data.message || 'Помилка додавання товару');
            }
        } catch (error) {
            console.error('Add to cart error:', error);
            this.showErrorMessage('Помилка додавання товару в кошик');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    async handleRemoveFromCart(button) {
        const productId = button.dataset.productId;
        const productName = button.dataset.productName || 'Товар';

        if (!productId) {
            return;
        }

        if (!confirm(`Видалити ${productName} з кошика?`)) {
            return;
        }

        this.setButtonLoading(button, true);

        try {
            const formData = new FormData();

            const response = await fetch(`/cart/remove/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Помилка сервера');
            }

            const data = await response.json();

            if (data.success) {
                this.showSuccessMessage(`${productName} видалено з кошика`);
                this.updateCartDisplay(data.cart);

                const cartRow = button.closest('.cart-item');
                if (cartRow) {
                    cartRow.style.opacity = '0';
                    setTimeout(() => {
                        cartRow.remove();
                        if (data.cart.total_items === 0) {
                            location.reload();
                        }
                    }, 300);
                }
            }
        } catch (error) {
            this.showErrorMessage('Помилка видалення товару');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    async handleQuantityButton(button) {
        const productId = button.dataset.productId;
        const action = button.dataset.action;
        const quantitySpan = document.querySelector(`.quantity-value[data-product-id="${productId}"]`);
        
        if (!productId || !quantitySpan) {
            return;
        }

        let currentQuantity = parseInt(quantitySpan.textContent);
        let newQuantity = currentQuantity;

        if (action === 'increase') {
            newQuantity = currentQuantity + 1;
        } else if (action === 'decrease') {
            newQuantity = currentQuantity - 1;
            if (newQuantity < 1) {
                return;
            }
        }

        button.disabled = true;

        try {
            const formData = new FormData();
            formData.append('quantity', newQuantity);
            formData.append('override', 'true');

            const response = await fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Помилка сервера');
            }

            const data = await response.json();

            if (data.success) {
                location.reload();
            }
        } catch (error) {
            this.showErrorMessage('Помилка оновлення кількості');
            button.disabled = false;
        }
    }

    async handleQuantityChange(input) {
        const productId = input.dataset.productId;
        const quantity = parseInt(input.value);

        if (!productId || quantity < 1) {
            return;
        }

        try {
            const formData = new FormData();
            formData.append('quantity', quantity);
            formData.append('override', 'true');

            const response = await fetch(`/cart/add/${productId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Помилка сервера');
            }

            const data = await response.json();

            if (data.success) {
                this.updateCartDisplay(data.cart);
                this.updateItemPrice(productId, data.item);
            }
        } catch (error) {
            this.showErrorMessage('Помилка оновлення кількості');
        }
    }

    async handleClearCart() {
        if (!confirm('Очистити кошик?')) {
            return;
        }

        try {
            const response = await fetch('/cart/clear/', {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCsrfToken(),
                },
            });

            if (!response.ok) {
                throw new Error('Помилка сервера');
            }

            const data = await response.json();

            if (data.success) {
                this.showSuccessMessage('Кошик очищено');
                location.reload();
            }
        } catch (error) {
            this.showErrorMessage('Помилка очищення кошика');
        }
    }

    getQuantityFromForm(button) {
        const form = button.closest('form');
        if (form) {
            const quantityInput = form.querySelector('input[name="quantity"]');
            return quantityInput ? parseInt(quantityInput.value) : 1;
        }
        
        const productDetail = button.closest('.product-detail, .product-info');
        if (productDetail) {
            const quantityInput = productDetail.querySelector('#productQuantity, .quantity-input');
            if (quantityInput) {
                return parseInt(quantityInput.value) || 1;
            }
        }
        
        return 1;
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Додаємо...';
            button.classList.add('loading');
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Купити';
            button.classList.remove('loading');
        }
    }

    updateCartDisplay(cartData) {
        if (!cartData) return;

        const cartBadges = document.querySelectorAll('.cart-badge, .cart-count');
        cartBadges.forEach((badge) => {
            if (cartData.item_count > 0) {
                badge.textContent = cartData.item_count;
                badge.style.display = 'flex';
            } else {
                badge.style.display = 'none';
            }
        });

        const cartTotals = document.querySelectorAll('.cart-total, .cart-grand-total');
        cartTotals.forEach((total) => {
            total.textContent = `${cartData.total_price.toFixed(2)} ₴`;
        });
    }

    updateItemPrice(productId, itemData) {
        if (!itemData || !productId) return;

        const cartItem = document.querySelector(`.cart-item[data-product-id="${productId}"]`);
        if (!cartItem) return;

        cartItem.dataset.price = itemData.price;

        const priceCurrentElement = cartItem.querySelector('.cart-item__price-current');
        if (priceCurrentElement) {
            priceCurrentElement.textContent = `${itemData.total.toFixed(2)} ₴`;
        }
    }

    animateCartIcon() {
        const cartIcon = document.querySelector('.cart-link, .header-action-link[href*="cart"]');
        if (cartIcon) {
            cartIcon.classList.add('cart-animation');
            setTimeout(() => {
                cartIcon.classList.remove('cart-animation');
            }, 600);
        }
    }

    showSuccessMessage(message) {
        this.showToast(message, 'success');
    }

    showErrorMessage(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'success') {
        const existingToasts = document.querySelectorAll('.cart-toast');
        existingToasts.forEach((toast) => toast.remove());

        const toast = document.createElement('div');
        toast.className = `cart-toast cart-toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');
        
        const icon = document.createElement('span');
        icon.className = 'cart-toast-icon';
        icon.textContent = type === 'success' ? '✓' : '✕';
        
        const text = document.createElement('span');
        text.className = 'cart-toast-text';
        text.textContent = message;
        
        toast.appendChild(icon);
        toast.appendChild(text);
        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.add('cart-toast-show');
        });

        setTimeout(() => {
            toast.classList.remove('cart-toast-show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    async handleApplyPromo() {
        const promoInput = document.getElementById('promo-code');
        const promoMessage = document.querySelector('.promo-message');
        const code = promoInput.value.trim();

        if (!code) {
            this.showPromoMessage('Введіть промокод', 'error');
            return;
        }

        try {
            const response = await fetch('/cart/apply-promo/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: `code=${encodeURIComponent(code)}`,
            });

            const data = await response.json();

            if (data.success) {
                this.showPromoMessage(data.message, 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showPromoMessage(data.message, 'error');
            }
        } catch (error) {
            this.showPromoMessage('Помилка застосування промокоду', 'error');
        }
    }

    showPromoMessage(message, type = 'info') {
        const promoMessage = document.querySelector('.promo-message');
        if (promoMessage) {
            promoMessage.textContent = message;
            promoMessage.className = `promo-message promo-message-${type}`;
            promoMessage.style.display = 'block';
            setTimeout(() => {
                promoMessage.style.display = 'none';
            }, 5000);
        }
    }

    getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input && input.value) {
            return input.value;
        }
        
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag && metaTag.content) {
            return metaTag.content;
        }
        
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith('csrftoken=')) {
                    return decodeURIComponent(cookie.substring('csrftoken='.length));
                }
            }
        }
        
        return '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.cart = new ShoppingCart();
});

