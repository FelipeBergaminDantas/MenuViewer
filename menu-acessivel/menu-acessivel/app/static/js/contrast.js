(function () {
    const STORAGE_KEY = "a11y-high-contrast";
    const root = document.documentElement;
    const btn = document.getElementById("btn-contrast");
    const sheet = document.getElementById("high-contrast-sheet");

    function setContrast(enabled) {
        root.classList.toggle("high-contrast", enabled);
        sheet.disabled = !enabled;
        btn.setAttribute("aria-pressed", enabled ? "true" : "false");
        localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");
    }

    setContrast(localStorage.getItem(STORAGE_KEY) === "1");

    btn.addEventListener("click", function () {
        const isEnabled = root.classList.contains("high-contrast");
        setContrast(!isEnabled);
    });
})();
