// Comandos de voz: liga o reconhecimento de fala do navegador (Web Speech API)
// às ações do cardápio. A interpretação das frases fica em interpretador.js.
//
// Decisões importantes:
// - Recurso opcional: os controles só aparecem se o navegador suportar.
// - Durante a resposta falada, o microfone é pausado, para o app não "ouvir a si mesmo".
// - Feedback sempre visual (balão de status) e para leitores de tela (#anuncios);
//   a resposta falada pode ser desligada (útil para quem já usa leitor de tela).
// - O estado "ligado" sobrevive à troca de página (ex.: próxima categoria no
//   modo simplificado) via sessionStorage.
import { anunciar } from "../anuncios.js";
import { interpretar, prepararComandos } from "./interpretador.js";

const CHAVE_SESSAO = "voz-ativa";

const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;

export function iniciarVoz() {
    const secao = document.querySelector("[data-voz]");
    const configEl = document.getElementById("voz-config");
    if (!secao || !configEl) return;

    if (!Reconhecimento) {
        secao.querySelector("[data-voz-sem-suporte]").hidden = false;
        return;
    }

    const config = JSON.parse(configEl.textContent);
    const controle = new ControleVoz(config, secao);
    controle.montar();
}

class ControleVoz {
    constructor(config, secao) {
        this.config = config;
        this.msgs = config.mensagens;
        this.comandos = prepararComandos(config.comandos);
        this.respostasFaladas = config.respostasFaladas;
        this.secao = secao;
        this.botao = secao.querySelector("[data-voz-alternar]");
        this.status = document.querySelector("[data-voz-status]");
        this.statusTexto = document.querySelector("[data-voz-status-texto]");
        this.ativo = false;
        this.falando = false;
        this.ouvindo = false;
        this.pratoAtual = -1;
        this.reconhecimento = null;
    }

    montar() {
        this.secao.querySelector("[data-voz-controles]").hidden = false;
        this.secao.querySelector("[data-voz-privacidade]").hidden = false;
        this.botao.addEventListener("click", () => (this.ativo ? this.desativar() : this.ativar()));

        document.addEventListener("preferencias:alteradas", (e) => {
            this.respostasFaladas = e.detail.voz_falada;
        });

        if (lerSessao()) this.ativar({ silencioso: true });
    }

    // ---------- Liga / desliga ----------

    ativar({ silencioso = false } = {}) {
        this.ativo = true;
        gravarSessao(true);
        this.botao.setAttribute("aria-pressed", "true");
        this.status.hidden = false;
        if (silencioso) {
            this.mostrarStatus(this.msgs.ouvindo);
            this.ouvir();
        } else {
            this.responder(this.msgs.ativado);
        }
    }

    desativar(mensagem = this.msgs.desativado) {
        this.ativo = false;
        gravarSessao(false);
        this.botao.setAttribute("aria-pressed", "false");
        this.pararDeOuvir();
        window.speechSynthesis?.cancel();
        this.status.hidden = true;
        this.status.classList.remove("ouvindo");
        anunciar(mensagem);
    }

    // ---------- Reconhecimento ----------

    ouvir() {
        if (!this.ativo || this.falando || this.ouvindo) return;

        const rec = new Reconhecimento();
        rec.lang = this.config.idioma;
        rec.continuous = false;
        rec.interimResults = false;
        rec.maxAlternatives = 3;

        rec.onstart = () => {
            this.ouvindo = true;
            this.status.classList.add("ouvindo");
        };
        rec.onresult = (evento) => this.aoReconhecer(evento.results[0]);
        rec.onerror = (evento) => this.aoErro(evento.error);
        rec.onend = () => {
            this.ouvindo = false;
            this.status.classList.remove("ouvindo");
            // O navegador encerra após cada frase ou silêncio; religamos enquanto ativo.
            if (this.ativo && !this.falando) window.setTimeout(() => this.ouvir(), 250);
        };

        this.reconhecimento = rec;
        try {
            rec.start();
        } catch {
            // start() lança se já estiver rodando; o onend religa depois.
        }
    }

    pararDeOuvir() {
        if (this.reconhecimento) {
            this.reconhecimento.onend = null;
            this.reconhecimento.abort();
            this.reconhecimento = null;
        }
        this.ouvindo = false;
    }

    aoErro(erro) {
        if (erro === "no-speech" || erro === "aborted") return; // onend religa
        if (erro === "not-allowed" || erro === "service-not-allowed") {
            this.desativar(this.msgs.permissao_negada);
            this.mostrarStatusTemporario(this.msgs.permissao_negada);
        } else if (erro === "audio-capture") {
            this.desativar(this.msgs.sem_microfone);
            this.mostrarStatusTemporario(this.msgs.sem_microfone);
        } else {
            this.desativar(this.msgs.erro);
            this.mostrarStatusTemporario(this.msgs.erro);
        }
    }

    aoReconhecer(resultado) {
        const pratos = this.pratosNaTela().map((el) => ({ id: el.id, nome: el.dataset.nome }));
        // Testa as alternativas do reconhecedor e fica com a primeira que faz sentido.
        let transcricao = resultado[0].transcript;
        let intencao = { acao: "desconhecido" };
        for (let i = 0; i < resultado.length; i++) {
            const tentativa = interpretar(resultado[i].transcript, this.comandos, pratos);
            if (tentativa.acao !== "desconhecido") {
                transcricao = resultado[i].transcript;
                intencao = tentativa;
                break;
            }
        }
        this.mostrarStatus(formatar(this.msgs.ouvi, { texto: transcricao.trim() }));
        this.executar(intencao, transcricao.trim());
    }

    // ---------- Ações ----------

    executar(intencao, transcricao) {
        const acoes = {
            abrir_cardapio: () => this.abrirCardapio(),
            mostrar_pratos: () => this.mostrarPratos(),
            proximo_prato: () => this.moverPrato(+1),
            prato_anterior: () => this.moverPrato(-1),
            proxima_categoria: () => this.moverCategoria(+1),
            categoria_anterior: () => this.moverCategoria(-1),
            selecionar: () => this.selecionar(this.indiceDoPrato(intencao.pratoId)),
            ler_descricao: () => this.lerDescricao(intencao.pratoId),
            mostrar_ingredientes: () => this.mostrarIngredientes(intencao.pratoId),
            ajuda: () => this.ajuda(),
            desativar: () => this.desativar(),
            prato_nao_encontrado: () =>
                this.responder(formatar(this.msgs.prato_nao_encontrado, { texto: intencao.texto })),
            desconhecido: () => this.responder(formatar(this.msgs.nao_entendi, { texto: transcricao })),
        };
        (acoes[intencao.acao] || acoes.desconhecido)();
    }

    pratosNaTela() {
        return [...document.querySelectorAll("[data-prato]")];
    }

    indiceDoPrato(id) {
        return this.pratosNaTela().findIndex((el) => el.id === id);
    }

    /** Prato atual: o que tem foco, ou o último selecionado por voz. */
    indiceAtual() {
        const pratos = this.pratosNaTela();
        const focado = document.activeElement?.closest?.("[data-prato]");
        if (focado) return pratos.indexOf(focado);
        return this.pratoAtual < pratos.length ? this.pratoAtual : -1;
    }

    abrirCardapio() {
        document.querySelector(".painel-a11y")?.removeAttribute("open");
        const titulo = document.querySelector("main h1");
        if (titulo) {
            titulo.setAttribute("tabindex", "-1");
            titulo.focus();
        }
        this.limparSelecao();
        this.responder(this.msgs.inicio);
    }

    mostrarPratos() {
        const pratos = this.pratosNaTela();
        if (!pratos.length) return this.responder(this.msgs.nenhum_prato);
        const nomes = pratos.map((el) => el.dataset.nome).join(", ");
        this.selecionar(0, { anunciar: false });
        this.responder(formatar(this.msgs.lista_pratos, { n: pratos.length, nomes }));
    }

    moverPrato(passo) {
        const pratos = this.pratosNaTela();
        if (!pratos.length) return this.responder(this.msgs.nenhum_prato);
        const atual = this.indiceAtual();
        const destino = atual === -1 ? (passo > 0 ? 0 : pratos.length - 1) : atual + passo;
        if (destino >= pratos.length) return this.responder(this.msgs.fim_da_lista);
        if (destino < 0) return this.responder(this.msgs.inicio_da_lista);
        this.selecionar(destino);
    }

    moverCategoria(passo) {
        // Modo simplificado: as categorias são páginas; seguimos o link.
        const link = document.querySelector(passo > 0 ? "[data-categoria-proxima]" : "[data-categoria-anterior]");
        if (link) {
            window.location.href = link.href;
            return;
        }
        const secoes = [...document.querySelectorAll("section.categoria")];
        if (secoes.length > 1) {
            const atualEl = this.pratosNaTela()[this.indiceAtual()];
            const atual = atualEl ? secoes.indexOf(atualEl.closest("section.categoria")) : -1;
            const destino = secoes[atual + passo] ?? (atual === -1 && passo > 0 ? secoes[0] : null);
            if (destino) {
                const primeiro = destino.querySelector("[data-prato]");
                if (primeiro) return this.selecionar(this.pratosNaTela().indexOf(primeiro));
            }
        }
        this.responder(passo > 0 ? this.msgs.sem_proxima_categoria : this.msgs.sem_categoria_anterior);
    }

    selecionar(indice, { anunciar: deveAnunciar = true } = {}) {
        const pratos = this.pratosNaTela();
        const el = pratos[indice];
        if (!el) return this.responder(this.msgs.sem_prato_selecionado);
        this.limparSelecao();
        this.pratoAtual = indice;
        el.classList.add("prato-atual");
        el.focus();
        if (deveAnunciar) {
            this.responder(formatar(this.msgs.prato_atual, { nome: el.dataset.nome, preco: precoDe(el) }));
        }
    }

    limparSelecao() {
        document.querySelectorAll(".prato-atual").forEach((el) => el.classList.remove("prato-atual"));
    }

    /** Prato alvo: o citado no comando, ou o atual. Seleciona-o se necessário. */
    alvo(pratoId) {
        const pratos = this.pratosNaTela();
        const indice = pratoId ? this.indiceDoPrato(pratoId) : this.indiceAtual();
        if (indice < 0) return null;
        if (indice !== this.indiceAtual()) this.selecionar(indice, { anunciar: false });
        return pratos[indice];
    }

    lerDescricao(pratoId) {
        const el = this.alvo(pratoId);
        if (!el) return this.responder(this.msgs.sem_prato_selecionado);
        const partes = [
            formatar(this.msgs.prato_atual, { nome: el.dataset.nome, preco: precoDe(el) }),
            el.querySelector("[data-descricao]")?.textContent.trim(),
            el.querySelector("[data-alergenos]")?.textContent.replace(/\s+/g, " ").trim(),
        ];
        this.responder(partes.filter(Boolean).join(" "));
    }

    mostrarIngredientes(pratoId) {
        const el = this.alvo(pratoId);
        if (!el) return this.responder(this.msgs.sem_prato_selecionado);
        const detalhes = el.querySelector("[data-ingredientes]");
        if (!detalhes) return this.responder(formatar(this.msgs.sem_ingredientes, { nome: el.dataset.nome }));
        detalhes.open = true;
        const lista = detalhes.querySelector("[data-lista-ingredientes]").textContent.trim();
        this.responder(formatar(this.msgs.ingredientes, { nome: el.dataset.nome, lista }));
    }

    ajuda() {
        const ajuda = this.secao.querySelector(".ajuda-voz");
        if (ajuda) ajuda.open = true;
        this.responder(this.msgs.ajuda);
    }

    // ---------- Feedback ----------

    responder(mensagem) {
        this.mostrarStatus(mensagem);
        anunciar(mensagem);
        if (this.respostasFaladas) this.falar(mensagem);
        else this.ouvir();
    }

    falar(texto) {
        const sintese = window.speechSynthesis;
        if (!sintese || !window.SpeechSynthesisUtterance) return this.ouvir();

        this.falando = true;
        this.pararDeOuvir();
        sintese.cancel();

        const fala = new SpeechSynthesisUtterance(texto);
        fala.lang = this.config.idioma;
        const retomar = () => {
            this.falando = false;
            if (this.ativo) this.ouvir();
        };
        fala.onend = retomar;
        fala.onerror = retomar;
        sintese.speak(fala);
    }

    mostrarStatus(texto) {
        if (this.statusTexto) this.statusTexto.textContent = texto;
    }

    mostrarStatusTemporario(texto) {
        this.status.hidden = false;
        this.mostrarStatus(texto);
        window.setTimeout(() => {
            if (!this.ativo) this.status.hidden = true;
        }, 6000);
    }
}

function precoDe(el) {
    return el.querySelector(".prato-preco data")?.textContent.trim() ?? "";
}

function formatar(modelo, valores) {
    return modelo.replace(/\{(\w+)\}/g, (_, chave) => (chave in valores ? valores[chave] : `{${chave}}`));
}

function lerSessao() {
    try {
        return window.sessionStorage.getItem(CHAVE_SESSAO) === "1";
    } catch {
        return false;
    }
}

function gravarSessao(ativo) {
    try {
        window.sessionStorage.setItem(CHAVE_SESSAO, ativo ? "1" : "0");
    } catch {
        // Armazenamento bloqueado: o recurso funciona, só não sobrevive à troca de página.
    }
}
