import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import LoaderManager from '../../utils/loader.js';
import { handleDialogKeydown } from '../../utils/dialog.js';

interface Category {
    id: number;
    name: string;
}

interface Preference {
    category_id: number;
    score: number;
}

export async function showPreferencesForm(categories: Category[]): Promise<void> {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const modal = document.createElement('div');
    modal.className = 'preferences-modal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'preferencesTitle');

    modal.innerHTML = `
        <form class="preferences-form">
            <h2 id="preferencesTitle" tabindex="-1">Let's Get to Know You Better</h2>
            <p class="preferences-description">
                To recommend you the most interesting products, tell us what you like.
                Rate each category using 2, 4, 6, 8, or 10, where 2 means low interest and 10 means very high interest.
            </p>
            <div class="preferences-list"></div>
            <button type="submit" class="btn submit-btn">Save preferences</button>
        </form>
    `;

    const preferencesList = modal.querySelector<HTMLElement>('.preferences-list')!;
    for (const { id, name } of categories) {
        const fieldset = document.createElement('fieldset');
        fieldset.className = 'preference-item';
        const legend = document.createElement('legend');
        legend.className = 'preference-title';
        legend.textContent = name;
        const ratingContainer = document.createElement('div');
        ratingContainer.className = 'rating-container';
        for (const score of [2, 4, 6, 8, 10]) {
            const label = document.createElement('label');
            label.className = 'rating-label';
            label.title = `Rating ${score}`;
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = `category_${id}`;
            input.value = String(score);
            const value = document.createElement('span');
            value.textContent = String(score);
            label.append(input, value);
            ratingContainer.appendChild(label);
        }
        fieldset.append(legend, ratingContainer);
        preferencesList.appendChild(fieldset);
    }

    document.body.appendChild(modal);
    const form = modal.querySelector('form') as HTMLFormElement;
    const title = modal.querySelector<HTMLElement>('#preferencesTitle');
    title?.focus();

    const closeModal = () => {
        modal.remove();
        previouslyFocused?.focus();
    };

    modal.addEventListener('keydown', (event) => handleDialogKeydown(event, modal, closeModal));

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const preferences: Preference[] = categories.map(({ id }) => {
            const selectedRating = form.querySelector(`input[name="category_${id}"]:checked`) as HTMLInputElement;
            return {
                category_id: id,
                score: selectedRating ? parseInt(selectedRating.value, 10) : 0,
            };
        });

        if (preferences.some(({ score }) => score === 0)) {
            NotificationManager.error('Please rate all categories');
            return;
        }

        const submitButton = form.querySelector<HTMLButtonElement>('button[type="submit"]');
        if (submitButton) submitButton.disabled = true;
        submitButton?.setAttribute('aria-busy', 'true');
        try {
            await LoaderManager.wrap(AuthService.savePreferences(preferences));
            NotificationManager.success('Thank you! Your preferences have been saved');
            modal.remove();
            window.location.href = '/pages/profile/index.html';
        } catch {
            NotificationManager.error('An error occurred while saving preferences');
            if (submitButton) submitButton.disabled = false;
            submitButton?.removeAttribute('aria-busy');
        }
    });
}
