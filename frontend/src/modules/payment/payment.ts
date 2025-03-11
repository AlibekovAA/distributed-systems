import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import LoaderManager from '../../utils/loader.js';
import type { Product } from '../../services/catalogService.js';

export async function showPaymentModal(cartItems: Product[], totalAmount: number): Promise<boolean> {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'payment-modal';

        let cartItemsHTML = '';
        cartItems.forEach(item => {
            cartItemsHTML += `
                <div class="cart-item">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-quantity">Quantity: ${item.quantity}</div>
                    <div class="cart-item-price">${item.price} ₽</div>
                </div>
            `;
        });

        modal.innerHTML = `
            <div class="payment-form">
                <h2>Payment</h2>
                <div class="cart-items">
                    ${cartItemsHTML}
                </div>
                <div class="payment-total">Total: ${totalAmount} ₽</div>

                <div class="payment-methods">
                    <label class="payment-method">
                        <input type="radio" name="payment-method" value="card1" checked>
                        <span class="payment-method-icon">💳</span>
                        <div class="payment-method-details">
                            <div class="payment-method-name">**** **** **** 1234</div>
                            <div class="payment-method-info">Expires 12/25</div>
                        </div>
                    </label>

                    <label class="payment-method">
                        <input type="radio" name="payment-method" value="card2">
                        <span class="payment-method-icon">💳</span>
                        <div class="payment-method-details">
                            <div class="payment-method-name">**** **** **** 5678</div>
                            <div class="payment-method-info">Expires 03/24</div>
                        </div>
                    </label>
                </div>

                <div class="add-balance-section">
                    <button class="add-balance-btn">Add 100,000 ₽ to Balance</button>
                </div>

                <div class="payment-actions">
                    <button class="cancel-btn">Cancel</button>
                    <button class="pay-btn">Pay ${totalAmount} ₽</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const addBalanceBtn = modal.querySelector('.add-balance-btn');
        addBalanceBtn?.addEventListener('click', async () => {
            try {
                await LoaderManager.wrap(AuthService.addBalance(100000));
                NotificationManager.success('Balance updated successfully');
            } catch (error) {
                NotificationManager.error('Failed to update balance');
            }
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
                resolve(false);
            }
        });

        const cancelBtn = modal.querySelector('.cancel-btn');
        cancelBtn?.addEventListener('click', () => {
            modal.remove();
            resolve(false);
        });

        const payBtn = modal.querySelector('.pay-btn');
        payBtn?.addEventListener('click', () => {
            modal.remove();
            resolve(true);
        });

        const paymentMethods = modal.querySelectorAll('.payment-method');
        paymentMethods.forEach(method => {
            method.addEventListener('click', () => {
                paymentMethods.forEach(m => m.classList.remove('selected'));
                method.classList.add('selected');
            });
        });
    });
}
