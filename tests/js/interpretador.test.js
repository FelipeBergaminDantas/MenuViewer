import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

import {
    encontrarPrato,
    interpretar,
    normalizar,
    prepararComandos,
} from "../../app/static/js/voz/interpretador.js";

// Usa as mesmas frases de produção, direto das traduções.
function comandosDe(idioma) {
    const url = new URL(`../../app/translations/${idioma}.json`, import.meta.url);
    return prepararComandos(JSON.parse(readFileSync(url, "utf-8")).voz.comandos);
}

const PRATOS = [
    { id: "prato-1", nome: "Bruschetta Clássica" },
    { id: "prato-2", nome: "Risoto de Funghi" },
    { id: "prato-3", nome: "Curry Picante de Grão-de-bico" },
    { id: "prato-4", nome: "Petit Gateau" },
    { id: "prato-5", nome: "Suco Natural de Laranja" },
    { id: "prato-6", nome: "Salmão Grelhado com Gergelim" },
];

describe("normalizar", () => {
    it("remove acentos, pontuação e caixa", () => {
        assert.equal(normalizar("  Próximo   PRATO!  "), "proximo prato");
        assert.equal(normalizar("Grão-de-bico"), "grao de bico");
    });
});

describe("interpretar (pt)", () => {
    const pt = comandosDe("pt");

    for (const [frase, acao] of [
        ["Abrir cardápio", "abrir_cardapio"],
        ["mostrar pratos", "mostrar_pratos"],
        ["Próximo prato", "proximo_prato"],
        ["Voltar", "prato_anterior"],
        ["mostrar ingredientes", "mostrar_ingredientes"],
        ["Ler descrição", "ler_descricao"],
        ["próxima categoria", "proxima_categoria"],
        ["categoria anterior", "categoria_anterior"],
        ["ajuda", "ajuda"],
        ["parar", "desativar"],
    ]) {
        it(`"${frase}" -> ${acao}`, () => {
            assert.equal(interpretar(frase, pt, PRATOS).acao, acao);
        });
    }

    it("prefere a frase mais longa ('categoria anterior' e não 'anterior')", () => {
        assert.equal(interpretar("voltar categoria", pt, PRATOS).acao, "categoria_anterior");
    });

    it("entende o comando dentro de uma frase maior", () => {
        assert.equal(interpretar("próximo prato por favor", pt, PRATOS).acao, "proximo_prato");
    });

    it("seleciona um prato com prefixo", () => {
        assert.deepEqual(interpretar("selecionar petit gateau", pt, PRATOS), {
            acao: "selecionar",
            pratoId: "prato-4",
        });
    });

    it("'mostrar <prato>' seleciona o prato em vez de listar pratos", () => {
        assert.deepEqual(interpretar("mostrar o risoto", pt, PRATOS), { acao: "selecionar", pratoId: "prato-2" });
    });

    it("seleciona um prato só pelo nome, mesmo parcial", () => {
        assert.deepEqual(interpretar("risoto", pt, PRATOS), { acao: "selecionar", pratoId: "prato-2" });
        assert.deepEqual(interpretar("curry", pt, PRATOS), { acao: "selecionar", pratoId: "prato-3" });
    });

    it("tolera pequenos erros de reconhecimento", () => {
        assert.equal(interpretar("risotto de fungi", pt, PRATOS).pratoId, "prato-2");
        assert.equal(interpretar("bruscheta", pt, PRATOS).pratoId, "prato-1");
    });

    it("comandos com alvo: 'mostrar ingredientes do salmão'", () => {
        assert.deepEqual(interpretar("mostrar ingredientes do salmão", pt, PRATOS), {
            acao: "mostrar_ingredientes",
            pratoId: "prato-6",
        });
        assert.deepEqual(interpretar("ler descrição do suco", pt, PRATOS), {
            acao: "ler_descricao",
            pratoId: "prato-5",
        });
    });

    it("prato inexistente com prefixo de seleção", () => {
        assert.deepEqual(interpretar("selecionar lasanha", pt, PRATOS), {
            acao: "prato_nao_encontrado",
            texto: "lasanha",
        });
    });

    it("frase sem sentido é desconhecida", () => {
        assert.equal(interpretar("qual a previsão do tempo", pt, PRATOS).acao, "desconhecido");
        assert.equal(interpretar("", pt, PRATOS).acao, "desconhecido");
    });
});

describe("interpretar (en/es)", () => {
    it("usa as frases do idioma da página", () => {
        assert.equal(interpretar("next dish", comandosDe("en"), PRATOS).acao, "proximo_prato");
        assert.equal(interpretar("go back", comandosDe("en"), PRATOS).acao, "prato_anterior");
        assert.equal(interpretar("siguiente plato", comandosDe("es"), PRATOS).acao, "proximo_prato");
        assert.equal(interpretar("mostrar ingredientes", comandosDe("es"), PRATOS).acao, "mostrar_ingredientes");
    });
});

describe("encontrarPrato", () => {
    it("não confunde pratos por palavras vazias", () => {
        assert.equal(encontrarPrato("de com", PRATOS), null);
    });
    it("exige que a maior parte do que foi dito corresponda", () => {
        assert.equal(encontrarPrato("suco de uva gelado com gelo", PRATOS), null);
    });
});
