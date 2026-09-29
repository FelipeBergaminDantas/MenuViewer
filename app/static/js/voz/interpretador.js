// Interpretador de comandos de voz — funções puras, sem DOM nem navegador,
// para poderem ser testadas com `node --test`.
//
// Recebe a frase reconhecida e devolve uma intenção, por exemplo:
//   "próximo prato"               -> { acao: "proximo_prato" }
//   "mostrar ingredientes do risoto" -> { acao: "mostrar_ingredientes", pratoId: "3" }
//   "selecionar petit gateau"     -> { acao: "selecionar", pratoId: "7" }
//   "risoto"                      -> { acao: "selecionar", pratoId: "3" }
//   "blá blá"                     -> { acao: "desconhecido" }
//
// As frases de cada comando vêm das traduções (voz.comandos.*), então o mesmo
// código funciona em qualquer idioma cadastrado.

// Palavras sem valor para identificar um prato.
const PALAVRAS_VAZIAS = new Set([
    "a", "o", "as", "os", "de", "do", "da", "dos", "das", "com", "ao", "e", "um", "uma", "no", "na",
    "the", "of", "with", "and", "an", "to",
    "el", "la", "los", "las", "del", "con", "y", "al",
]);

const LIMIAR_PRATO = 0.6;

/** Minúsculas, sem acentos e sem pontuação, com espaços normalizados. */
export function normalizar(texto) {
    return String(texto)
        .toLowerCase()
        .normalize("NFD")
        .replace(/[̀-ͯ]/g, "")
        .replace(/[^\p{L}\p{N}\s-]/gu, " ")
        .replace(/-/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function palavras(texto) {
    return normalizar(texto).split(" ").filter((p) => p && !PALAVRAS_VAZIAS.has(p));
}

/** Similaridade entre 0 e 1 baseada na distância de Levenshtein. */
export function similaridade(a, b) {
    if (a === b) return 1;
    if (!a.length || !b.length) return 0;
    let anterior = Array.from({ length: b.length + 1 }, (_, i) => i);
    for (let i = 1; i <= a.length; i++) {
        const atual = [i];
        for (let j = 1; j <= b.length; j++) {
            const custo = a[i - 1] === b[j - 1] ? 0 : 1;
            atual[j] = Math.min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + custo);
        }
        anterior = atual;
    }
    return 1 - anterior[b.length] / Math.max(a.length, b.length);
}

function palavraCorresponde(falada, doPrato) {
    if (falada === doPrato) return true;
    // Plural/singular e reconhecimento parcial: "cogumelo" ~ "cogumelos".
    if (falada.length >= 4 && doPrato.length >= 4 && (doPrato.startsWith(falada) || falada.startsWith(doPrato))) {
        return true;
    }
    return falada.length >= 4 && similaridade(falada, doPrato) >= 0.75;
}

/**
 * Encontra o prato cujo nome melhor corresponde ao texto falado.
 * @param {string} texto
 * @param {{id: string, nome: string}[]} pratos
 * @returns {string|null} id do prato
 */
export function encontrarPrato(texto, pratos) {
    const faladas = palavras(texto);
    if (!faladas.length) return null;

    let melhor = null;
    for (const prato of pratos) {
        const doPrato = palavras(prato.nome);
        if (!doPrato.length) continue;
        const acertos = faladas.filter((f) => doPrato.some((p) => palavraCorresponde(f, p))).length;
        if (!acertos) continue;
        // Quanto do que foi dito bate com o prato, e quanto do nome do prato foi dito.
        const precisao = acertos / faladas.length;
        const cobertura = acertos / doPrato.length;
        const nota = precisao * 0.7 + cobertura * 0.3;
        if (precisao >= LIMIAR_PRATO && (!melhor || nota > melhor.nota)) {
            melhor = { id: prato.id, nota };
        }
    }
    return melhor ? melhor.id : null;
}

/** Procura `frase` como sequência de palavras inteiras dentro de `texto`. */
function posicaoDaFrase(texto, frase) {
    const alvo = ` ${texto} `;
    const indice = alvo.indexOf(` ${frase} `);
    return indice === -1 ? null : { inicio: indice, fim: indice + frase.length };
}

/**
 * Prepara as frases de comando (normalizadas, da mais longa para a mais curta,
 * para que "categoria anterior" vença "anterior").
 * @param {Record<string, string[]>} comandos
 */
export function prepararComandos(comandos) {
    const frases = [];
    const prefixosSelecao = [];
    for (const [acao, lista] of Object.entries(comandos)) {
        for (const frase of lista) {
            const normalizada = normalizar(frase);
            if (!normalizada) continue;
            if (acao === "selecionar") prefixosSelecao.push(normalizada);
            else frases.push({ acao, frase: normalizada });
        }
    }
    frases.sort((a, b) => b.frase.length - a.frase.length);
    prefixosSelecao.sort((a, b) => b.length - a.length);
    return { frases, prefixosSelecao };
}

// Comandos que podem mirar um prato específico: "ler descrição do risoto".
const ACOES_COM_ALVO = new Set(["ler_descricao", "mostrar_ingredientes"]);

/**
 * @param {string} transcricao frase reconhecida
 * @param {ReturnType<typeof prepararComandos>} preparados
 * @param {{id: string, nome: string}[]} pratos pratos visíveis na página
 */
export function interpretar(transcricao, preparados, pratos = []) {
    const texto = normalizar(transcricao);
    if (!texto) return { acao: "desconhecido" };

    // 1. Frase exata de um comando.
    const exato = preparados.frases.find((f) => f.frase === texto);
    if (exato) return { acao: exato.acao };

    // 2. "Selecionar <prato>" — antes do passo 3, para "mostrar risoto" não
    //    virar "mostrar pratos" por engano.
    for (const prefixo of preparados.prefixosSelecao) {
        if (texto.startsWith(`${prefixo} `)) {
            const resto = texto.slice(prefixo.length + 1);
            const pratoId = encontrarPrato(resto, pratos);
            if (pratoId) return { acao: "selecionar", pratoId };
        }
    }

    // 3. Frase de comando dentro de uma fala maior ("próximo prato, por favor").
    for (const { acao, frase } of preparados.frases) {
        const posicao = posicaoDaFrase(texto, frase);
        if (!posicao) continue;
        const resultado = { acao };
        if (ACOES_COM_ALVO.has(acao)) {
            const resto = `${texto.slice(0, posicao.inicio)} ${texto.slice(posicao.fim)}`;
            const pratoId = encontrarPrato(resto, pratos);
            if (pratoId) resultado.pratoId = pratoId;
        }
        return resultado;
    }

    // 4. Só o nome de um prato.
    const pratoId = encontrarPrato(texto, pratos);
    if (pratoId) return { acao: "selecionar", pratoId };

    // 5. Prefixo de seleção com um prato que não existe na tela.
    const prefixo = preparados.prefixosSelecao.find((p) => texto.startsWith(`${p} `));
    if (prefixo) return { acao: "prato_nao_encontrado", texto: texto.slice(prefixo.length + 1) };

    return { acao: "desconhecido" };
}
