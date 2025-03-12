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
                    <div class="cart-item-price">${item.price} ₽</div>
                </div>
            `;
        });

        modal.innerHTML = `
            <div class="payment-form">
                <h2>Payment</h2>
                <div class="payment-total">Total: ${totalAmount} ₽</div>

                <div class="card-form">
                    <div class="form-group">
                        <label>Card Number</label>
                        <input type="text"
                               class="card-input"
                               placeholder="**** **** **** ****"
                               maxlength="19"
                               autocomplete="off">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Expiry Date</label>
                            <input type="text"
                                   class="card-input"
                                   placeholder="MM/YY"
                                   maxlength="5"
                                   autocomplete="off">
                        </div>
                        <div class="form-group">
                            <label>CVV</label>
                            <input type="text"
                                   class="card-input"
                                   placeholder="***"
                                   maxlength="3"
                                   autocomplete="off">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Cardholder Name</label>
                        <input type="text"
                               class="card-input"
                               placeholder="JOHN DOE"
                               autocomplete="off">
                    </div>
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

        const cardNumberInput = modal.querySelector('input[placeholder="**** **** **** ****"]');
        if (cardNumberInput) {
            cardNumberInput.addEventListener('input', (e) => {
                const input = e.target as HTMLInputElement;
                let value = input.value.replace(/\D/g, '');
                value = value.replace(/(\d{4})/g, '$1 ').trim();
                input.value = value;
            });
        }

        const expiryInput = modal.querySelector('input[placeholder="MM/YY"]');
        if (expiryInput) {
            expiryInput.addEventListener('input', (e) => {
                const input = e.target as HTMLInputElement;
                let value = input.value.replace(/\D/g, '');
                if (value.length >= 2) {
                    value = value.slice(0, 2) + '/' + value.slice(2);
                }
                input.value = value;
            });
        }
    });
}
