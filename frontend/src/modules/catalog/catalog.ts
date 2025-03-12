import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

function createProductCard({ id, name, description, price, quantity }: any): HTMLElement {
    const productCard = document.createElement('div');
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

    const cartIcon = document.createElement('span');
    cartIcon.className = 'cart-icon';
    cartIcon.textContent = '🛒';

    addToCartButton.appendChild(cartIcon);
    addToCartButton.appendChild(document.createTextNode(' Add to Cart'));

    productCard.appendChild(productInfo);
    productCard.appendChild(addToCartButton);

    return productCard;
}

function handleAddToCartClick(event: Event): void {
    const target = event.target as HTMLElement | null;
    if (!target) return;

    const button = target.closest('.add-to-cart-btn');
    if (!(button instanceof HTMLButtonElement)) return;

    const productId = button.dataset.productId;
    if (!productId) return;

    LoaderManager.wrap(CatalogService.addToCart(Number(productId)))
        .then(() => NotificationManager.success('Product added to cart'))
        .catch(() => NotificationManager.error('Failed to add product to cart'));
}

async function initializeCatalog() {
    if (!await authGuard()) return;

    const catalogContent = document.querySelector('.catalog-content');
    if (!catalogContent) return;

    try {
        const products = await LoaderManager.wrap(CatalogService.getProducts(), true);
        const productsGrid = document.createElement('div');
        productsGrid.className = 'products-grid';

        products.forEach((product: any) => {
            const productCard = createProductCard(product);
            productsGrid.appendChild(productCard);
        });

        catalogContent.appendChild(productsGrid);

        productsGrid.addEventListener('click', handleAddToCartClick);

    } catch (error) {
        NotificationManager.error('Failed to load product catalog');
        console.error('Catalog loading error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeCatalog);
