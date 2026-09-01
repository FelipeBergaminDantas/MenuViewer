(function () {
    const STORAGE_KEY = "a11y-lang";
    const buttons = document.querySelectorAll(".flag-btn");
    const cache = {};

    function loadLocale(lang) {
        if (cache[lang]) return Promise.resolve(cache[lang]);
        return fetch(`/static/locales/${lang}.json`)
            .then((res) => res.json())
            .then((data) => {
                cache[lang] = data;
                return data;
            });
    }

    function applyLocale(dict) {
        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            const key = el.dataset.i18n;
            if (dict[key]) el.textContent = dict[key];
        });
    }

    function setLang(lang) {
        localStorage.setItem(STORAGE_KEY, lang);
        document.documentElement.lang = lang;
        buttons.forEach((b) => b.setAttribute("aria-pressed", b.dataset.lang === lang ? "true" : "false"));
        loadLocale(lang).then(applyLocale).catch(() => {
            // Se o arquivo de idioma não existir ainda, mantém o texto padrão em pt-BR.
        });
    }

    buttons.forEach(function (btn) {
        btn.addEventListener("click", function () {
            setLang(btn.dataset.lang);
        });
    });

    setLang(localStorage.getItem(STORAGE_KEY) || "pt");
})();
