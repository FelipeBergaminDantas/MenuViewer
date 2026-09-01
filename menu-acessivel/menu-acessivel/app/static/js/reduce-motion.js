(function () {
    const STORAGE_KEY = "a11y-reduce-motion";
    const root = document.documentElement;
    const btn = document.getElementById("btn-reduce-motion");

    function setReduceMotion(enabled) {
        root.classList.toggle("reduce-motion", enabled);
        btn.setAttribute("aria-pressed", enabled ? "true" : "false");
        localStorage.setItem(STORAGE_KEY, enabled ? "1" : "0");
    }

    setReduceMotion(localStorage.getItem(STORAGE_KEY) === "1");

    btn.addEventListener("click", function () {
        const isEnabled = root.classList.contains("reduce-motion");
        setReduceMotion(!isEnabled);
    });
})();
