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

        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';

        productsGrid.innerHTML = products.map(({ id, name, description, price, quantity }) => `
            <div class="product-card">
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
            </div>
        `).join('');

        catalogContent.appendChild(productsGrid);

        productsGrid.addEventListener('click', async (e) => {
            const target = e.target as HTMLElement;
            const button = target.closest('.add-to-cart-btn');
            if (!button) return;

            const productId = button.getAttribute('data-product-id');
            if (!productId) return;

            try {
                await LoaderManager.wrap(CatalogService.addToCart(Number(productId)));
                NotificationManager.success('Product added to cart');
            } catch (error) {
                NotificationManager.error('Failed to add product to cart');
            }
        });
    } catch (error) {
        NotificationManager.error('Failed to load product catalog');
        console.error('Catalog loading error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeCatalog);
