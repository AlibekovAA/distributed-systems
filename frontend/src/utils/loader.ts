class LoaderManager {
    private static overlay: HTMLElement | null = null;
    private static showTimeout: number | null = null;

    private static createLoader(): HTMLElement {
        if (this.overlay) return this.overlay;

        const overlay = document.createElement('div');
        overlay.className = 'loader-overlay';

        const loader = document.createElement('div');
        loader.className = 'loader';

        Array.from({ length: 3 }).forEach(() => {
            const dot = document.createElement('div');
            dot.className = 'loader-dot';
            loader.appendChild(dot);
        });

        overlay.appendChild(loader);
        document.body.appendChild(overlay);
        return (this.overlay = overlay);
    }

    static show(immediate = false): void {
        const overlay = this.createLoader();

        if (this.showTimeout) {
            clearTimeout(this.showTimeout);
            this.showTimeout = null;
        }

        if (immediate) {
            overlay.classList.add('visible');
        } else {
            this.showTimeout = window.setTimeout(() => overlay.classList.add('visible'), 300);
        }
    }

    static hide(): void {
        if (this.showTimeout) {
            clearTimeout(this.showTimeout);
            this.showTimeout = null;
        }

        this.overlay?.classList.remove('visible');
        setTimeout(() => {
            this.overlay?.remove();
            this.overlay = null;
        }, 300);
    }

    static async wrap<T>(promise: Promise<T>, immediate = false): Promise<T> {
        this.show(immediate);
        try {
            return await promise;
        } finally {
            this.hide();
        }
    }
}

export default LoaderManager;
