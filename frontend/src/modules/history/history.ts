import { CatalogService } from '../../services/catalogService.js';
import NotificationManager from '../../utils/notifications.js';
import { authGuard } from '../../utils/authGuard.js';
import LoaderManager from '../../utils/loader.js';
import { initializeLogout } from '../../utils/logout.js';
import { createEmptyStateIcon } from '../../utils/stateIcon.js';

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

function createGroupedItems(order: Order): DocumentFragment {
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

    const fragment = document.createDocumentFragment();
    Object.values(groupedItems).forEach((item) => {
        const orderItem = document.createElement('div');
        orderItem.className = 'order-item';

        const itemInfo = document.createElement('div');
        itemInfo.className = 'item-info';

        const itemName = document.createElement('div');
        itemName.className = 'cart-item-name';
        itemName.textContent = item.name;

        const itemQuantity = document.createElement('div');
        itemQuantity.className = 'cart-item-quantity';
        itemQuantity.textContent = `Quantity: ${item.quantity}`;

        const itemPrice = document.createElement('div');
        itemPrice.className = 'cart-item-price';
        itemPrice.textContent = `${item.total} ₽`;

        itemInfo.append(itemName, itemQuantity, itemPrice);
        orderItem.appendChild(itemInfo);
        fragment.appendChild(orderItem);
    });
    return fragment;
}

function createOrderElement(order: Order): HTMLElement {
    const orderGroup = document.createElement('div');
    orderGroup.className = 'order-group';

    const orderHeader = document.createElement('div');
    orderHeader.className = 'order-header';

    const orderTitle = document.createElement('h3');
    orderTitle.textContent = `Order #${order.order_number}`;

    const orderTotal = document.createElement('span');
    orderTotal.className = 'order-total';
    orderTotal.textContent = `Total: ${order.total_price} ₽`;

    const orderItems = document.createElement('div');
    orderItems.className = 'order-items';
    orderItems.appendChild(createGroupedItems(order));

    orderHeader.append(orderTitle, orderTotal);
    orderGroup.append(orderHeader, orderItems);
    return orderGroup;
}

function createHistoryState(type: 'empty' | 'error'): HTMLElement {
    const panel = document.createElement('div');
    panel.className = 'state-panel';
    panel.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = type === 'empty' ? createEmptyStateIcon() : document.createElement('div');
    if (type === 'error') {
        icon.className = 'state-icon';
        icon.setAttribute('aria-hidden', 'true');
        icon.textContent = '!';
    }

    const title = document.createElement('h2');
    title.textContent = type === 'empty' ? 'History is empty' : "Couldn't load purchase history";

    const description = document.createElement('p');
    description.textContent = type === 'empty'
        ? 'You have not made any purchases yet'
        : 'Check your connection and try again.';

    panel.append(icon, title, description);
    if (type === 'empty') {
        const link = document.createElement('a');
        link.href = '/pages/catalog/index.html';
        link.className = 'btn go-to-catalog-btn';
        link.textContent = 'Go to Catalog';
        panel.appendChild(link);
    } else {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn retry-btn';
        button.textContent = 'Try Again';
        button.addEventListener('click', initializeHistory, { once: true });
        panel.appendChild(button);
    }
    return panel;
}

async function initializeHistory() {
    if (!authGuard()) return;

    const historyContent = document.querySelector('.history-content');
    if (!historyContent) return;
    const historyContainer = document.querySelector('.history-container');
    historyContainer?.setAttribute('aria-busy', 'true');

    try {
        const orders = await LoaderManager.wrap(CatalogService.getOrderHistory(), true);

        if (!orders || orders.length === 0) {
            const title = document.createElement('h1');
            title.textContent = 'Purchase History';
            historyContent.replaceChildren(title, createHistoryState('empty'));
            return;
        }

        const title = document.createElement('h1');
        title.textContent = 'Purchase History';

        const ordersContainer = document.createElement('div');
        ordersContainer.className = 'orders-container';
        orders
            .sort((a, b) => b.order_number - a.order_number)
            .forEach((order) => ordersContainer.appendChild(createOrderElement(order)));

        historyContent.replaceChildren(title, ordersContainer);

    } catch {
        NotificationManager.error("Couldn't load purchase history");
        const title = document.createElement('h1');
        title.textContent = 'Purchase History';
        historyContent.replaceChildren(title, createHistoryState('error'));
    } finally {
        historyContainer?.setAttribute('aria-busy', 'false');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initializeLogout();
    initializeHistory();
});
