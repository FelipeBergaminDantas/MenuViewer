// Foto ampliada em <dialog> nativo: showModal() cuida de prender o foco,
// fechar com Esc e tornar o resto da página inerte.
export function iniciarFotoAmpliada() {
    const dialogo = document.getElementById("dialogo-foto");
    if (!dialogo || typeof dialogo.showModal !== "function") {
        // Sem suporte a <dialog>: os botões não fariam nada, então saem da página.
        document.querySelectorAll("[data-ampliar-foto]").forEach((b) => b.remove());
        return;
    }

    const titulo = dialogo.querySelector("[data-dialogo-titulo]");
    const imagem = dialogo.querySelector("[data-dialogo-imagem]");
    let origem = null;

    document.addEventListener("click", (evento) => {
        const botao = evento.target.closest("[data-ampliar-foto]");
        if (!botao) return;
        origem = botao;
        titulo.textContent = botao.dataset.titulo;
        imagem.src = botao.dataset.src;
        imagem.alt = botao.dataset.alt;
        dialogo.showModal();
    });

    // Clique no fundo escurecido (fora do conteúdo) fecha.
    dialogo.addEventListener("click", (evento) => {
        if (evento.target === dialogo) dialogo.close();
    });

    dialogo.addEventListener("close", () => {
        imagem.removeAttribute("src");
        // Navegadores modernos já devolvem o foco; garantimos para os demais.
        if (origem && document.activeElement !== origem) origem.focus();
    });
}
