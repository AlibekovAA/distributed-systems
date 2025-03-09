import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

async function initializeCatalog() {
    if (!await authGuard()) return;

    const catalogContent = document.querySelector('.catalog-content');
    if (!catalogContent) return;

    try {
        const products = await LoaderManager.wrap(CatalogService.getProducts(), true);
        const fragment = document.createDocumentFragment();
        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';

        products.forEach(({ id, name, description, price, quantity }) => {
            const productCard = document.createElement('div');
            productCard.className = 'product-card';
            productCard.innerHTML = `
                <div class="product-info">
                    <div class="product-name">${name}</div>
                    <div class="product-description">${description}</div>
                    <div class="product-details">
                        <div class="product-price">${price} ₽</div>
                        <div class="product-quantity">In stock: ${quantity} pcs.</div>
                    </div>
                </div>
                <button class="add-to-cart-btn" data-product-id="${id}">
                    <span class="cart-icon">🛒</span>
                    Add to Cart
                </button>
            `;
            fragment.appendChild(productCard);
        });

        productsGrid.appendChild(fragment);
        catalogContent.appendChild(productsGrid);

        productsGrid.addEventListener('click', async (event) => {
            const target = event.target as HTMLElement | null;
            if (!target) return;

            const button = target.closest('.add-to-cart-btn');
            if (!(button instanceof HTMLButtonElement)) return;

            const productId = button.dataset.productId;
            if (!productId) return;

            try {
                await LoaderManager.wrap(CatalogService.addToCart(Number(productId)));
                NotificationManager.success('Product added to cart');
            } catch {
                NotificationManager.error('Failed to add product to cart');
            }
        });

    } catch (error) {
        NotificationManager.error('Failed to load product catalog');
        console.error('Catalog loading error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeCatalog);
