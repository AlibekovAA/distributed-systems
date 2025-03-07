import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

async function initializeCart() {
    if (!await authGuard()) return;

    const cartContent = document.querySelector('.cart-content');
    if (!cartContent) return;

    try {
        const cartItems = await LoaderManager.wrap(CatalogService.getCart(), true);

        if (!cartItems.length) {
            cartContent.innerHTML = `
                <div class="empty-cart">
                    <div class="empty-cart-icon">🛒</div>
                    <h2>Your Cart is Empty</h2>
                    <p>Browse our catalog to find products you like</p>
                    <a href="/pages/catalog/index.html" class="btn go-to-catalog-btn">
                        Go to Catalog
                    </a>
                </div>
            `;
            return;
        }

        const totalPrice = cartItems.reduce((sum, item) => sum + item.price, 0);

        cartContent.innerHTML = `
            <h1>Shopping Cart</h1>
            <div class="cart-items">
                ${cartItems.map(item => `
                    <div class="cart-item">
                        <div class="cart-item-info">
                            <div class="cart-item-name">${item.name}</div>
                            <div class="cart-item-price">${item.price} ₽</div>
                        </div>
                        <button class="remove-from-cart-btn" data-product-id="${item.id}">
                            ✕
                        </button>
                    </div>
                `).join('')}
            </div>
            <div class="cart-summary">
                <div class="cart-total">
                    <span>Total:</span>
                    <span>${totalPrice} ₽</span>
                </div>
                <button class="btn checkout-btn">Checkout</button>
            </div>
        `;

        cartContent.addEventListener('click', async (e) => {
            const target = e.target as HTMLElement;
            const removeButton = target.closest('.remove-from-cart-btn');
            if (!removeButton) return;

            const productId = removeButton.getAttribute('data-product-id');
            if (!productId) return;

            try {
                await LoaderManager.wrap(CatalogService.removeFromCart(Number(productId)));
                NotificationManager.success('Product removed from cart');
                initializeCart();
            } catch (error) {
                NotificationManager.error('Failed to remove product from cart');
            }
        });
    } catch (error) {
        NotificationManager.error('Failed to load shopping cart');
        console.error('Cart loading error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeCart);
