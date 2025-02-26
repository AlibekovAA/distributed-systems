type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationOptions {
    message: string;
    type: NotificationType;
    duration?: number;
}

class NotificationManager {
    private static container: HTMLDivElement | null = null;

    private static createContainer(): HTMLDivElement {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
        this.container = container;
        return container;
    }

    private static getContainer(): HTMLDivElement {
        return this.container ?? this.createContainer();
    }

    static show({ message, type, duration = 3000 }: NotificationOptions): void {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;

        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getIconForType(type)}</span>
                <span class="notification-message">${message}</span>
            </div>
        `;

        const container = this.getContainer();
        container.appendChild(notification);

        requestAnimationFrame(() => notification.classList.add('show'));

        setTimeout(() => this.hideNotification(notification), duration);
    }

    private static hideNotification(notification: HTMLDivElement): void {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }

    private static getIconForType(type: NotificationType): string {
        const icons: Record<NotificationType, string> = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type];
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
