import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';
import { initializeLogout } from '../../utils/logout.js';

function createProductCard({ id, name, description, price, quantity }: any): HTMLElement {
    const productCard = document.createElement('article');
    productCard.className = 'product-card';

    const productInfo = document.createElement('div');
    productInfo.className = 'product-info';

    const productName = document.createElement('div');
    productName.className = 'product-name';
    productName.textContent = name;

    const productDescription = document.createElement('div');
    productDescription.className = 'product-description';
    productDescription.textContent = description;

    const productDetails = document.createElement('div');
    productDetails.className = 'product-details';

    const productPrice = document.createElement('div');
    productPrice.className = 'product-price';
    productPrice.textContent = `${price} ₽`;

    const productQuantity = document.createElement('div');
    productQuantity.className = 'product-quantity';
    productQuantity.textContent = `In stock: ${quantity} pcs.`;

    productDetails.appendChild(productPrice);
    productDetails.appendChild(productQuantity);
    productInfo.appendChild(productName);
    productInfo.appendChild(productDescription);
    productInfo.appendChild(productDetails);

    const addToCartButton = document.createElement('button');
    addToCartButton.className = 'add-to-cart-btn';
    addToCartButton.dataset.productId = String(id);
    addToCartButton.setAttribute('aria-label', `Add ${name} to cart`);

    const cartIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    cartIcon.setAttribute('class', 'cart-icon');
    cartIcon.setAttribute('viewBox', '0 0 24 24');
    cartIcon.setAttribute('fill', 'none');
    cartIcon.setAttribute('stroke', 'currentColor');
    cartIcon.setAttribute('stroke-width', '2');
    cartIcon.setAttribute('aria-hidden', 'true');
    const cartPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    cartPath.setAttribute('d', 'M3 4h2l2.5 11h10l2-7H6M9 19h.01M17 19h.01');
    cartIcon.appendChild(cartPath);

    addToCartButton.appendChild(cartIcon);
    addToCartButton.appendChild(document.createTextNode('Add to Cart'));

    productCard.appendChild(productInfo);
    productCard.appendChild(addToCartButton);

    return productCard;
}

async function handleAddToCartClick(event: Event): Promise<void> {
    const target = event.target as HTMLElement | null;
    if (!target) return;

    const button = target.closest('.add-to-cart-btn');
    if (!(button instanceof HTMLButtonElement)) return;

    const productId = button.dataset.productId;
    if (!productId) return;

    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    try {
        await LoaderManager.wrap(CatalogService.addToCart(Number(productId)));
        NotificationManager.success('Product added to cart');
    } catch {
        NotificationManager.error('Failed to add product to cart');
    } finally {
        button.disabled = false;
        button.removeAttribute('aria-busy');
    }
}

function createStatePanel(type: 'empty' | 'error', retry?: () => void): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'state-panel';
    panel.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = document.createElement('div');
    icon.className = 'state-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = type === 'empty' ? '□' : '!';

    const title = document.createElement('h2');
    title.textContent = type === 'empty' ? 'Catalog is empty' : "Couldn't load product catalog";

    const description = document.createElement('p');
    description.textContent = type === 'empty'
        ? 'Products will appear here when they become available.'
        : 'Check your connection and try again.';

    panel.append(icon, title, description);
    if (retry) {
        const button = document.createElement('button');
        button.className = 'btn retry-btn';
        button.type = 'button';
        button.textContent = 'Try Again';
        button.addEventListener('click', retry, { once: true });
        panel.appendChild(button);
    }
    return panel;
}

async function initializeCatalog() {
    if (!await authGuard()) return;

    const catalogContent = document.querySelector('.catalog-content');
    if (!catalogContent) return;
    const catalogContainer = document.querySelector('.catalog-container');
    catalogContainer?.setAttribute('aria-busy', 'true');

    try {
        const products = await LoaderManager.wrap(CatalogService.getProducts(), true);
        catalogContent.querySelector('.products-grid, .state-panel')?.remove();

        if (!products.length) {
            catalogContent.appendChild(createStatePanel('empty'));
            return;
        }

        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';

        products.forEach((product: any) => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });

        catalogContent.appendChild(productsGrid);

        productsGrid.addEventListener('click', handleAddToCartClick);

    } catch {
        NotificationManager.error('Failed to load product catalog');
        catalogContent.querySelector('.products-grid, .state-panel')?.remove();
        catalogContent.appendChild(createStatePanel('error', initializeCatalog));
    } finally {
        catalogContainer?.setAttribute('aria-busy', 'false');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeLogout();
    initializeCatalog();
});
