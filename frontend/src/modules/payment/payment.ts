import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import LoaderManager from '../../utils/loader.js';
import { handleDialogKeydown } from '../../utils/dialog.js';

export async function showPaymentModal(totalAmount: number): Promise<boolean> {
    return new Promise((resolve) => {
        const previouslyFocused = document.activeElement as HTMLElement | null;
        const modal = document.createElement('div');
        modal.className = 'payment-modal';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'paymentTitle');

        modal.innerHTML = `
            <div class="payment-form">
                <h2 id="paymentTitle">Payment</h2>
                <div class="payment-total">Total: <span class="payment-total-value"></span></div>

                <div class="card-form">
                    <div class="form-group">
                        <label for="cardNumber">Card Number</label>
                        <input type="text"
                               id="cardNumber"
                               class="card-input"
                               placeholder="**** **** **** ****"
                               maxlength="19"
                               inputmode="numeric"
                               autocomplete="off">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label for="expiryDate">Expiry Date</label>
                            <input type="text"
                                   id="expiryDate"
                                   class="card-input"
                                   placeholder="MM/YY"
                                   maxlength="5"
                                   inputmode="numeric"
                                   autocomplete="off">
                        </div>
                        <div class="form-group">
                            <label for="cardCvv">CVV</label>
                            <input type="text"
                                   id="cardCvv"
                                   class="card-input"
                                   placeholder="***"
                                   maxlength="3"
                                   inputmode="numeric"
                                   autocomplete="off">
                        </div>
                    </div>
                    <div class="form-group">
                        <label for="cardholderName">Cardholder Name</label>
                        <input type="text"
                               id="cardholderName"
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
                    <button class="pay-btn">Pay <span class="payment-button-total"></span></button>
                </div>
            </div>
        `;

        modal.querySelector<HTMLElement>('.payment-total-value')!.textContent = `${totalAmount} ₽`;
        modal.querySelector<HTMLElement>('.payment-button-total')!.textContent = `${totalAmount} ₽`;

        document.body.appendChild(modal);
        modal.querySelector<HTMLInputElement>('#cardNumber')?.focus();

        const closeModal = (result: boolean) => {
            modal.remove();
            previouslyFocused?.focus();
            resolve(result);
        };

        modal.addEventListener('keydown', (event) => handleDialogKeydown(event, modal, () => closeModal(false)));

        const addBalanceBtn = modal.querySelector('.add-balance-btn');
        addBalanceBtn?.addEventListener('click', async () => {
            if (!(addBalanceBtn instanceof HTMLButtonElement)) return;
            addBalanceBtn.disabled = true;
            addBalanceBtn.setAttribute('aria-busy', 'true');
            try {
                await LoaderManager.wrap(AuthService.addBalance(100000));
                NotificationManager.success('Balance updated successfully');
            } catch {
                NotificationManager.error('Failed to update balance');
            } finally {
                addBalanceBtn.disabled = false;
                addBalanceBtn.removeAttribute('aria-busy');
            }
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal(false);
            }
        });

        const cancelBtn = modal.querySelector('.cancel-btn');
        cancelBtn?.addEventListener('click', () => {
            closeModal(false);
        });

        const payBtn = modal.querySelector('.pay-btn');
        payBtn?.addEventListener('click', () => {
            closeModal(true);
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
