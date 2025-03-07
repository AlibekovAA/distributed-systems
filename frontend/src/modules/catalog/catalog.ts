import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

async function initializeCatalog() {
    if (!await authGuard()) return;

    const catalogContent = document.querySelector('.catalog-content');
    if (!catalogContent) return;

    try {
        const products = await LoaderManager.wrap(CatalogService.getProducts());

        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';

        productsGrid.innerHTML = products.map(({ name, description, price, quantity }) => `
            <div class="product-card">
                <div class="product-name">${name}</div>
                <div class="product-description">${description}</div>
                <div class="product-price">${price} ₽</div>
                <div class="product-quantity">In stock: ${quantity} pcs.</div>
            </div>
        `).join('');

        catalogContent.appendChild(productsGrid);
    } catch (error) {
        NotificationManager.error('Failed to load the product catalog');
        console.error('Catalog loading error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeCatalog);
