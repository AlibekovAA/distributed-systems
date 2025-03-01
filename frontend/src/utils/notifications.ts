type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationOptions {
    message: string;
    type: NotificationType;
    duration?: number;
}

const ICONS: Record<NotificationType, string> = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
};

class NotificationManager {
    private static container: HTMLDivElement | null = null;

    private static createContainer(): HTMLDivElement {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
        return (this.container = container);
    }

    private static getContainer(): HTMLDivElement {
        return this.container ?? this.createContainer();
    }

    static show({ message, type, duration = 3000 }: NotificationOptions): void {
        const container = this.getContainer();
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'assertive');

        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${ICONS[type]}</span>
                <span class="notification-message">${message}</span>
            </div>
        `;

        container.appendChild(notification);
        requestAnimationFrame(() => notification.classList.add('show'));

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    static success(message: string, duration?: number) {
        this.show({ message, type: 'success', duration });
    }

    static error(message: string, duration?: number) {
        this.show({ message, type: 'error', duration });
    }

    static warning(message: string, duration?: number) {
        this.show({ message, type: 'warning', duration });
    }

    static info(message: string, duration?: number) {
        this.show({ message, type: 'info', duration });
    }
}

export default NotificationManager;
