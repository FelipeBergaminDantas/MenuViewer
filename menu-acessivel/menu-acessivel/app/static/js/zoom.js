(function () {
    const overlay = document.getElementById("zoom-overlay");
    const overlayImg = document.getElementById("zoom-image");
    const closeBtn = document.getElementById("zoom-close");
    let lastFocused = null;

    function openZoom(imgSrc, altText, triggerEl) {
        if (!imgSrc) return;
        lastFocused = triggerEl;
        overlayImg.src = imgSrc;
        overlayImg.alt = altText;
        overlay.classList.remove("hidden");
        closeBtn.focus();
        document.addEventListener("keydown", onKeydown);
    }

    function closeZoom() {
        overlay.classList.add("hidden");
        overlayImg.src = "";
        document.removeEventListener("keydown", onKeydown);
        if (lastFocused) lastFocused.focus();
    }

    function onKeydown(e) {
        if (e.key === "Escape") closeZoom();
    }

    document.querySelectorAll(".zoomable").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const img = btn.querySelector("img");
            openZoom(btn.dataset.img, img ? img.alt : "", btn);
        });
    });

    closeBtn.addEventListener("click", closeZoom);
    overlay.addEventListener("click", function (e) {
        if (e.target === overlay) closeZoom();
    });
})();
