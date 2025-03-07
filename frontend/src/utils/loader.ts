class LoaderManager {
    private static overlay: HTMLElement | null = null;
    private static showTimeout: NodeJS.Timeout | null = null;

    private static createLoader() {
        const overlay = document.createElement('div');
        overlay.className = 'loader-overlay';

        const loader = document.createElement('div');
        loader.className = 'loader';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'loader-dot';
            loader.appendChild(dot);
        }

        overlay.appendChild(loader);
        document.body.appendChild(overlay);
        return overlay;
    }

    private static getOverlay() {
        if (!this.overlay) {
            this.overlay = this.createLoader();
        }
        return this.overlay;
    }

    static show(immediate = false) {
        const overlay = this.getOverlay();

        if (this.showTimeout) {
            clearTimeout(this.showTimeout);
            this.showTimeout = null;
        }

        if (immediate) {
            overlay.classList.add('visible');
        } else {
            this.showTimeout = setTimeout(() => {
                overlay.classList.add('visible');
            }, 300);
        }
    }

    static hide() {
        if (this.showTimeout) {
            clearTimeout(this.showTimeout);
            this.showTimeout = null;
        }

        if (this.overlay) {
            this.overlay.classList.remove('visible');
        }
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
