import { CatalogService } from '../../services/catalogService.js';
import type { Product } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

async function initializeCart() {
    if (!await authGuard()) return;

    const cartContent = document.querySelector('.cart-content');
    if (!cartContent) return;

    try {
        const cartItems = await LoaderManager.wrap(CatalogService.getCart(), true);

        cartContent.innerHTML = '';

        if (!Array.isArray(cartItems) || cartItems.length === 0) {
            const emptyCart = document.createElement('div');
            emptyCart.className = 'empty-cart';
            emptyCart.innerHTML = `
                <div class="empty-cart-icon">🛒</div>
                <h2>Your Cart is Empty</h2>
                <p>Browse our catalog to find products you like</p>
                <a href="/pages/catalog/index.html" class="btn go-to-catalog-btn">Go to Catalog</a>
            `;
            cartContent.appendChild(emptyCart);
            return;
        }

        const fragment = document.createDocumentFragment();

        const title = document.createElement('h1');
        title.textContent = 'Shopping Cart';
        fragment.appendChild(title);

        const cartItemsContainer = document.createElement('div');
        cartItemsContainer.className = 'cart-items';

        let totalPrice = 0;

        cartItems.forEach(({ id, name, price }) => {
            totalPrice += price;

            const cartItem = document.createElement('div');
            cartItem.className = 'cart-item';
            cartItem.innerHTML = `
                <div class="cart-item-info">
                    <div class="cart-item-name">${name}</div>
                    <div class="cart-item-price">${price} ₽</div>
                </div>
                <button class="remove-from-cart-btn" data-product-id="${id}">✕</button>
            `;
            cartItemsContainer.appendChild(cartItem);
        });

        fragment.appendChild(cartItemsContainer);

        const cartSummary = document.createElement('div');
        cartSummary.className = 'cart-summary';
        cartSummary.innerHTML = `
            <div class="cart-total">
                <span>Total:</span>
                <span>${totalPrice} ₽</span>
            </div>
            <button class="pay-for-order-btn">Pay for Order</button>
        `;
        fragment.appendChild(cartSummary);

        cartContent.appendChild(fragment);

        cartContent.addEventListener('click', async (event) => {
            const target = event.target as HTMLElement | null;
            if (!target) return;

            if (target.closest('.pay-for-order-btn')) {
                if (!localStorage.getItem('access_token')) {
                    NotificationManager.error('Not authenticated');
                    return;
                }

                try {
                    await handlePayment(cartItems);
                } catch {
                    NotificationManager.error('Failed to pay for order');
                }
                return;
            }

            const removeButton = target.closest('.remove-from-cart-btn') as HTMLElement | null;
            if (removeButton) {
                const productId = removeButton.dataset.productId;
                if (!productId) return;

                try {
                    await LoaderManager.wrap(CatalogService.removeFromCart(Number(productId)));
                    NotificationManager.success('Product removed from cart');
                    initializeCart();
                } catch {
                    NotificationManager.error('Failed to remove product from cart');
                }
            }
        });
    } catch (error) {
        console.error('Error loading cart:', error);
        NotificationManager.error('Failed to load shopping cart');

        cartContent.innerHTML = `
            <div class="empty-cart">
                <div class="empty-cart-icon">🛒</div>
                <h2>Your Cart is Empty</h2>
                <p>Browse our catalog to find products you like</p>
                <a href="/pages/catalog/index.html" class="btn go-to-catalog-btn">Go to Catalog</a>
            </div>
        `;
    }
}

async function handlePayment(cartItems: Product[]) {
    try {
        await LoaderManager.wrap(CatalogService.payForOrder(cartItems));
        NotificationManager.success('Order paid successfully');
        setTimeout(() => window.location.reload(), 1500);
    } catch (error) {
        if (error instanceof Error && error.message === 'insufficient_funds') {
            NotificationManager.error('Insufficient funds. Please top up your balance in the profile.');

            const cartSummary = document.querySelector('.cart-summary');
            if (cartSummary) {
                const existingBtn = cartSummary.querySelector('.go-to-profile-btn');
                if (existingBtn) {
                    existingBtn.remove();
                }

                const goToProfileBtn = document.createElement('button');
                goToProfileBtn.className = 'btn go-to-profile-btn';
                goToProfileBtn.textContent = 'Go to balance top-up';
                goToProfileBtn.onclick = () => window.location.href = '/pages/profile/index.html';

                cartSummary.appendChild(goToProfileBtn);
            }
        } else {
            NotificationManager.error('An error occurred while paying for the order');
        }
    }
}

document.addEventListener('DOMContentLoaded', initializeCart);
