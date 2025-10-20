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
            const removeBtn = e.target.closest('.remove-from-cart, .btn-remove-from-cart');
            if (removeBtn) {
                e.preventDefault();
                this.handleRemoveFromCart(removeBtn);
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
    }

    async handleAddToCart(button) {
        const productId = button.dataset.productId;
        const productName = button.dataset.productName || 'Товар';
        const quantity = this.getQuantityFromForm(button) || 1;

        if (!productId) {
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
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Помилка сервера');
            }

            const data = await response.json();

            if (data.success) {
                this.showSuccessMessage(`${productName} додано в кошик`);
                this.updateCartDisplay(data.cart);
                this.animateCartIcon();
            } else {
                this.showErrorMessage(data.message || 'Помилка додавання товару');
            }
        } catch (error) {
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
                this.updateItemPrice(input, data.item);
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

    updateItemPrice(quantityInput, itemData) {
        if (!itemData) return;

        const cartItem = quantityInput.closest('.cart-item');
        if (!cartItem) return;

        cartItem.dataset.price = itemData.price;

        const priceElement = cartItem.querySelector('.item-price');
        if (priceElement) {
            priceElement.textContent = `${itemData.price.toFixed(2)} ₴`;
        }

        const totalElement = cartItem.querySelector('.item-total .total-price');
        if (totalElement) {
            totalElement.textContent = `${itemData.total.toFixed(2)} ₴`;
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
        this.showMessage(message, 'success');
    }

    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type = 'info') {
        const existingMessages = document.querySelectorAll('.cart-message');
        existingMessages.forEach((msg) => msg.remove());

        const messageDiv = document.createElement('div');
        messageDiv.className = `cart-message cart-message-${type}`;
        messageDiv.textContent = message;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.classList.add('show');
        }, 10);

        setTimeout(() => {
            messageDiv.classList.remove('show');
            setTimeout(() => messageDiv.remove(), 300);
        }, 3000);
    }

    getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) {
            return token.value;
        }
        const cookie = document.cookie
            .split('; ')
            .find((row) => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.cart = new ShoppingCart();
});

