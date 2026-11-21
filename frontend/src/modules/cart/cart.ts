import { CatalogApiError, CatalogService } from '../../services/catalogService.js';
import type { Product } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';
import { showPaymentModal } from '../payment/payment.js';
import { initializeLogout } from '../../utils/logout.js';

interface GroupedProduct extends Product {
    quantity: number;
    totalPrice: number;
}

let currentCartItems: Product[] = [];

function groupCartItems(cartItems: Product[]): GroupedProduct[] {
    const groupedItems = cartItems.reduce<Record<string, GroupedProduct>>((acc, item) => {
        const key = String(item.id);
        if (!acc[key]) {
            acc[key] = { ...item, quantity: 0, totalPrice: 0 };
        }
        acc[key].quantity += 1;
        acc[key].totalPrice = acc[key].price * acc[key].quantity;
        return acc;
    }, {});
    return Object.values(groupedItems);
}

function createEmptyState(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'state-panel';
    panel.setAttribute('role', 'status');

    const icon = document.createElement('div');
    icon.className = 'state-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '□';

    const title = document.createElement('h2');
    title.textContent = 'Your Cart is Empty';

    const description = document.createElement('p');
    description.textContent = 'Browse our catalog to find products you like';

    const link = document.createElement('a');
    link.href = '/pages/catalog/index.html';
    link.className = 'btn go-to-catalog-btn';
    link.textContent = 'Go to Catalog';

    panel.append(icon, title, description, link);
    return panel;
}

function createErrorState(): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'state-panel';
    panel.setAttribute('role', 'alert');

    const icon = document.createElement('div');
    icon.className = 'state-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = '!';

    const title = document.createElement('h2');
    title.textContent = "Couldn't load shopping cart";

    const description = document.createElement('p');
    description.textContent = 'Check your connection and try again.';

    const retryButton = document.createElement('button');
    retryButton.type = 'button';
    retryButton.className = 'btn retry-btn';
    retryButton.textContent = 'Try Again';

    panel.append(icon, title, description, retryButton);
    return panel;
}

function createCartItem(item: GroupedProduct): HTMLElement {
    const cartItem = document.createElement('div');
    cartItem.className = 'cart-item';

    const itemInfo = document.createElement('div');
    itemInfo.className = 'cart-item-info';

    const itemName = document.createElement('div');
    itemName.className = 'cart-item-name';
    itemName.textContent = item.name;

    const itemQuantity = document.createElement('div');
    itemQuantity.className = 'cart-item-quantity';
    itemQuantity.textContent = `Quantity: ${item.quantity}`;

    const itemPrice = document.createElement('div');
    itemPrice.className = 'cart-item-price';
    itemPrice.textContent = `${item.totalPrice} ₽`;

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-from-cart-btn';
    removeButton.dataset.productId = String(item.id);
    removeButton.setAttribute('aria-label', `Remove ${item.name} from cart`);
    removeButton.textContent = '×';

    itemInfo.append(itemName, itemQuantity, itemPrice);
    cartItem.append(itemInfo, removeButton);
    return cartItem;
}

function createCartSummary(totalPrice: number): HTMLElement {
    const summary = document.createElement('div');
    summary.className = 'cart-summary';

    const total = document.createElement('div');
    total.className = 'cart-total';
    const label = document.createElement('span');
    label.textContent = 'Total:';
    const value = document.createElement('span');
    value.textContent = `${totalPrice} ₽`;
    total.append(label, value);

    const payButton = document.createElement('button');
    payButton.type = 'button';
    payButton.className = 'pay-for-order-btn';
    payButton.setAttribute('aria-haspopup', 'dialog');
    payButton.textContent = 'Pay for Order';

    summary.append(total, payButton);
    return summary;
}

function renderCart(container: HTMLElement, cartItems: Product[]): void {
    if (!cartItems.length) {
        container.replaceChildren(createEmptyState());
        return;
    }

    const groupedItems = groupCartItems(cartItems);
    const cartItemsElement = document.createElement('div');
    cartItemsElement.className = 'cart-items';
    groupedItems.forEach((item) => cartItemsElement.appendChild(createCartItem(item)));

    const totalPrice = groupedItems.reduce((sum, item) => sum + item.totalPrice, 0);
    container.replaceChildren(cartItemsElement, createCartSummary(totalPrice));
}

async function initializeCart() {
    if (!authGuard()) return;

    const cartItemsContainer = document.querySelector('.cart-items-container');
    if (!(cartItemsContainer instanceof HTMLElement)) return;
    const cartContainer = document.querySelector('.cart-container');
    cartContainer?.setAttribute('aria-busy', 'true');

    try {
        const cartItems = await LoaderManager.wrap(CatalogService.getCart(), true);
        currentCartItems = Array.isArray(cartItems) ? cartItems : [];
        renderCart(cartItemsContainer, currentCartItems);
    } catch {
        NotificationManager.error('Failed to load shopping cart');
        currentCartItems = [];
        cartItemsContainer.replaceChildren(createErrorState());
    } finally {
        cartContainer?.setAttribute('aria-busy', 'false');
    }
}

async function handleCartClick(event: Event): Promise<void> {
    const target = event.target as HTMLElement | null;
    if (!target) return;

    const retryButton = target.closest('.retry-btn') as HTMLButtonElement | null;
    if (retryButton) {
        retryButton.disabled = true;
        await initializeCart();
        return;
    }

    const payButton = target.closest('.pay-for-order-btn') as HTMLButtonElement | null;
    if (payButton) {
        if (!localStorage.getItem('access_token')) {
            NotificationManager.error('Not authenticated');
            return;
        }
        try {
            await handlePayment(currentCartItems, payButton);
        } catch {
            NotificationManager.error('Failed to pay for order');
        }
        return;
    }

    const removeButton = target.closest('.remove-from-cart-btn') as HTMLButtonElement | null;
    if (!removeButton) return;
    const productId = removeButton.dataset.productId;
    if (!productId) return;

    removeButton.disabled = true;
    removeButton.setAttribute('aria-busy', 'true');
    try {
        await LoaderManager.wrap(CatalogService.removeFromCart(Number(productId)));
        NotificationManager.success('Product removed from cart');
        await initializeCart();
    } catch {
        NotificationManager.error('Failed to remove product from cart');
        removeButton.disabled = false;
        removeButton.removeAttribute('aria-busy');
    }
}

async function handlePayment(cartItems: Product[], sourceButton: HTMLButtonElement): Promise<void> {
    try {
        const totalPrice = cartItems.reduce((sum, item) => sum + item.price, 0);
        const shouldProceed = await showPaymentModal(totalPrice);

        if (!shouldProceed) return;
        sourceButton.disabled = true;
        sourceButton.setAttribute('aria-busy', 'true');

        try {
            await LoaderManager.wrap(CatalogService.payForOrder());
            NotificationManager.success('Order paid successfully');
            setTimeout(() => window.location.reload(), 500);
        } catch (error) {
            if (error instanceof CatalogApiError && error.payload.error === 'insufficient_funds') {
                NotificationManager.error('Insufficient funds. Please add more money to your balance.');
            } else {
                NotificationManager.error('An error occurred while paying for the order');
            }
        } finally {
            sourceButton.disabled = false;
            sourceButton.removeAttribute('aria-busy');
            sourceButton.focus();
        }
    } catch (error) {
        NotificationManager.error('An error occurred while processing payment');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeLogout();
    document.querySelector('.cart-items-container')?.addEventListener('click', handleCartClick);
    initializeCart();
});
