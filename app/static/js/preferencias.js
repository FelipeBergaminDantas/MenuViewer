// Aplica as preferências de acessibilidade sem recarregar a página.
// O servidor continua sendo a fonte da verdade: enviamos o mesmo formulário via
// fetch, ele valida, grava o cookie e devolve o novo estado para aplicarmos.
// Se algo falhar, o formulário segue o caminho normal (recarrega a página).
import { anunciar } from "./anuncios.js";

const CLASSES_DE_MODO = ["alto-contraste", "movimento-reduzido", "modo-simplificado"];

export function iniciarPreferencias() {
    document.querySelectorAll("[data-form-preferencias]").forEach((form) => {
        form.addEventListener("submit", (evento) => enviar(evento, form));
    });
}

async function enviar(evento, form) {
    const botao = evento.submitter;
    // Mudanças de layout (ex.: modo simplificado) precisam do HTML novo do servidor.
    if (!botao || botao.hasAttribute("data-recarregar")) return;

    evento.preventDefault();
    const dados = new FormData(form, botao);

    try {
        const resposta = await fetch(form.action, {
            method: "POST",
            body: dados,
            headers: { Accept: "application/json" },
            credentials: "same-origin",
        });
        if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
        aplicar(await resposta.json());
    } catch {
        form.submit();
    }
}

function aplicar(prefs) {
    const html = document.documentElement;
    html.style.setProperty("--escala-fonte", prefs.fonte);
    const ativas = new Set(prefs.classes.split(" ").filter(Boolean));
    CLASSES_DE_MODO.forEach((classe) => html.classList.toggle(classe, ativas.has(classe)));

    document.querySelectorAll("[data-saida-fonte]").forEach((el) => {
        el.textContent = `${prefs.fonte_percentual}%`;
    });
    for (const chave of ["contraste", "movimento_reduzido", "simplificado", "voz_falada"]) {
        document
            .querySelectorAll(`[data-form-preferencias] button[value="${chave}"]`)
            .forEach((b) => b.setAttribute("aria-pressed", String(prefs[chave])));
    }

    document.dispatchEvent(new CustomEvent("preferencias:alteradas", { detail: prefs }));
    anunciar(prefs.anuncio);
}
