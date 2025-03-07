class LoaderManager {
    private static overlay: HTMLElement | null = null;
    private static showTimeout?: NodeJS.Timeout;

    private static createLoader(): HTMLElement {
        const overlay = document.createElement('div');
        overlay.className = 'loader-overlay';
        overlay.innerHTML = `
            <div class="loader">
                ${Array(3).fill('<div class="loader-dot"></div>').join('')}
            </div>
        `;
        document.body.appendChild(overlay);
        return overlay;
    }

    private static show(): void {
        if (!this.overlay) {
            this.overlay = this.createLoader();
            requestAnimationFrame(() => this.overlay?.classList.add('visible'));
        }
    }

    private static hide(): void {
        this.overlay?.classList.remove('visible');
        setTimeout(() => {
            this.overlay?.remove();
            this.overlay = null;
        }, 300);

        clearTimeout(this.showTimeout);
    }

    static async wrap<T>(promise: Promise<T>): Promise<T> {
        this.showTimeout = setTimeout(this.show.bind(this), 1000);

        try {
            return await promise;
        } finally {
            this.hide();
        }
    }
}

export default LoaderManager;
