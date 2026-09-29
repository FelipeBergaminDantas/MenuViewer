// Após uma navegação iniciada pelo usuário (aplicar filtro, mudar de categoria
// no modo simplificado), leva o foco ao elemento marcado pelo servidor, para
// que o leitor de tela anuncie o resultado em vez de recomeçar do topo.
export function iniciarFocoInicial() {
    const alvo = document.querySelector("[data-focar-ao-carregar]");
    if (alvo) alvo.focus();
}
