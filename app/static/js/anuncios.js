// Envia mensagens curtas para a região aria-live da página (#anuncios).
const regiao = () => document.getElementById("anuncios");

export function anunciar(mensagem) {
    const el = regiao();
    if (!el || !mensagem) return;
    // Limpar antes garante que a mesma mensagem repetida seja anunciada de novo.
    el.textContent = "";
    window.setTimeout(() => { el.textContent = mensagem; }, 50);
}
