(function () {
    const STORAGE_KEY = "a11y-font-scale";
    const MIN_SCALE = 0.85;
    const MAX_SCALE = 1.6;
    const STEP = 0.1;

    const root = document.documentElement;

    function applyScale(scale) {
        root.style.setProperty("--font-scale", scale);
        localStorage.setItem(STORAGE_KEY, scale);
    }

    function getCurrentScale() {
        const saved = parseFloat(localStorage.getItem(STORAGE_KEY));
        return isNaN(saved) ? 1 : saved;
    }

    applyScale(getCurrentScale());

    document.getElementById("btn-font-increase").addEventListener("click", function () {
        const next = Math.min(MAX_SCALE, getCurrentScale() + STEP);
        applyScale(next);
    });

    document.getElementById("btn-font-decrease").addEventListener("click", function () {
        const next = Math.max(MIN_SCALE, getCurrentScale() - STEP);
        applyScale(next);
    });

    document.getElementById("btn-font-reset").addEventListener("click", function () {
        applyScale(1);
    });
})();
