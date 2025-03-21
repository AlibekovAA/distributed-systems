import { AuthService } from '../../services/authService.js';
import NotificationManager from '../../utils/notifications.js';
import LoaderManager from '../../utils/loader.js';

interface Category {
    id: number;
    name: string;
}

interface Preference {
    category_id: number;
    score: number;
}

export async function showPreferencesForm(categories: Category[]): Promise<void> {
    const modal = document.createElement('div');
    modal.className = 'preferences-modal';

    const categoryItems = categories
        .map(({ id, name }) => {
            const ratingOptions = [2, 4, 6, 8, 10]
                .map((score) => `
                    <label class="rating-label" title="Rating ${score}">
                        <input type="radio" name="category_${id}" value="${score}">
                        <span>${score}</span>
                    </label>
                `).join('');

            return `
                <div class="preference-item">
                    <label>${name}</label>
                    <div class="rating-container">${ratingOptions}</div>
                </div>
            `;
        })
        .join('');

    modal.innerHTML = `
        <form class="preferences-form">
            <h2>Let's Get to Know You Better</h2>
            <p class="preferences-description">
                To recommend you the most interesting products, tell us what you like.
                Rate each category on a scale from 1 to 10, where 1 means not interested at all, and 10 means very interested.
            </p>
            <div class="preferences-list">${categoryItems}</div>
            <button type="submit" class="btn submit-btn">Save preferences</button>
        </form>
    `;

    document.body.appendChild(modal);
    const form = modal.querySelector('form') as HTMLFormElement;

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

        try {
            await LoaderManager.wrap(AuthService.savePreferences(preferences));
            NotificationManager.success('Thank you! Your preferences have been saved');
            modal.remove();
            window.location.href = '/pages/profile/index.html';
        } catch {
            NotificationManager.error('An error occurred while saving preferences');
        }
    });
}
