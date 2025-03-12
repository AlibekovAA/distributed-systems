import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';

interface GroupedItem {
    name: string;
    description: string;
    price: number;
    quantity: number;
    total: number;
}

interface OrderItem {
    name: string;
    description: string;
    price: number;
}

interface Order {
    items: OrderItem[];
    order_number: number;
    total_price: number;
}

function formatGroupedItems(order: Order): string {
    const groupedItems = order.items.reduce((acc: Record<string, GroupedItem>, item: OrderItem) => {
        const key = `${item.name}-${item.price}`;
        if (!acc[key]) {
            acc[key] = {
                name: item.name,
                description: item.description,
                price: item.price,
                quantity: 0,
                total: 0
            };
        }
        acc[key].quantity += 1;
        acc[key].total = acc[key].price * acc[key].quantity;
        return acc;
    }, {});

    return Object.values(groupedItems)
        .map(item => `
            <div class="order-item">
                <div class="item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-quantity">Quantity: ${item.quantity}</div>
                    <div class="cart-item-price">${item.total} ₽</div>
                </div>
            </div>
        `).join('');
}

function generateOrderHTML(order: any): string {
    const itemsHTML = formatGroupedItems(order);
    return `
        <div class="order-group">
            <div class="order-header">
                <h3>Order #${order.order_number}</h3>
                <span class="order-total">Total: ${order.total_price} ₽</span>
            </div>
            <div class="order-items">
                ${itemsHTML}
            </div>
        </div>
    `;
}

function generateEmptyHistoryHTML(): string {
    return `
        <h1>Purchase History</h1>
        <div class="empty-history">
            <div class="empty-history-icon">📋</div>
            <h2>History is empty</h2>
            <p>You have not made any purchases yet</p>
            <a href="/pages/catalog/index.html" class="btn go-to-catalog-btn">Go to catalog</a>
        </div>
    `;
}

async function initializeHistory() {
    if (!await authGuard()) return;

    const historyContent = document.querySelector('.history-content');
    if (!historyContent) return;

    try {
        const orders = await LoaderManager.wrap(CatalogService.getOrderHistory(), true);

        if (!orders || orders.length === 0) {
            historyContent.innerHTML = generateEmptyHistoryHTML();
            return;
        }

        const ordersHTML = orders
            .sort((a, b) => b.order_number - a.order_number)
            .map(generateOrderHTML)
            .join('');

        historyContent.innerHTML = `
            <h1>Purchase History</h1>
            <div class="orders-container">
                ${ordersHTML}
            </div>
        `;

    } catch (error) {
        console.error('Error loading history:', error);
        NotificationManager.error("Couldn't load purchase history");
    }
}

document.addEventListener('DOMContentLoaded', initializeHistory);
