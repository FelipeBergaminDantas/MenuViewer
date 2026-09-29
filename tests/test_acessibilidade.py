"""Verificações estruturais de acessibilidade (issue de teclado / tecnologias assistivas).

Cobrem o que dá para garantir no HTML gerado pelo servidor. O comportamento
visual do foco e a ordem real de tabulação são verificados em navegador
(ver docs/CONTRIBUTING.md → "Checklist manual de acessibilidade").
"""

import re
from pathlib import Path

import pytest

URLS = ["/", "/?sem=gluten&aplicado=1", "/qrcode"]


@pytest.fixture(params=["padrao", "simplificado"])
def paginas(request, client, pagina, definir_prefs):
    definir_prefs(simplificado=request.param == "simplificado")
    return [pagina(url) for url in URLS]


def nome_acessivel(el):
    """Aproximação do nome acessível: aria-label, texto visível ou alt de imagem interna."""
    if el.get("aria-label"):
        return el["aria-label"].strip()
    if el.get("aria-labelledby"):
        return "labelledby"
    texto = el.get_text(" ", strip=True)
    if texto:
        return texto
    img = el.find("img")
    return img.get("alt", "").strip() if img else ""


def test_idioma_da_pagina_declarado(paginas):
    for soup in paginas:
        assert soup.html.get("lang")


def test_ids_unicos(paginas):
    for soup in paginas:
        ids = [el["id"] for el in soup.select("[id]")]
        assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]


def test_referencias_aria_apontam_para_elementos_existentes(paginas):
    for soup in paginas:
        for atributo in ("aria-labelledby", "aria-describedby"):
            for el in soup.select(f"[{atributo}]"):
                for alvo in el[atributo].split():
                    assert soup.find(id=alvo), f"{atributo}='{alvo}' não existe"


def test_todo_elemento_interativo_tem_nome_acessivel(paginas):
    for soup in paginas:
        for el in soup.select("a[href], button, summary"):
            assert nome_acessivel(el), f"sem nome acessível: {el}"


def test_campos_de_formulario_tem_rotulo(paginas):
    for soup in paginas:
        for campo in soup.select("input:not([type=hidden]), select, textarea"):
            rotulado = campo.find_parent("label") or (
                campo.get("id") and soup.select_one(f"label[for='{campo['id']}']")
            )
            assert rotulado or campo.get("aria-label"), f"campo sem rótulo: {campo}"


def test_imagens_tem_alt(paginas):
    for soup in paginas:
        for img in soup.find_all("img"):
            assert img.has_attr("alt"), img


def test_sem_tabindex_positivo(paginas):
    """tabindex > 0 quebra a ordem natural de tabulação."""
    for soup in paginas:
        for el in soup.select("[tabindex]"):
            assert int(el["tabindex"]) <= 0, el


def test_sem_elementos_falsos_interativos(paginas):
    """Cliques só em elementos nativamente focáveis (button/a/summary/input)."""
    for soup in paginas:
        assert soup.select("[onclick]") == []
        assert soup.select("div[role=button], span[role=button], a:not([href])") == []


def test_botoes_dentro_de_forms_declaram_tipo(paginas):
    for soup in paginas:
        for botao in soup.find_all("button"):
            assert botao.get("type") in ("button", "submit"), botao


def test_estado_dos_botoes_de_alternar(paginas):
    for soup in paginas:
        for botao in soup.select(".btn-alternar"):
            assert botao.get("aria-pressed") in ("true", "false"), botao


def test_hierarquia_de_titulos_sem_saltos(paginas):
    for soup in paginas:
        niveis = [int(h.name[1]) for h in soup.find_all(re.compile(r"^h[1-6]$"))
                  if not h.find_parent("dialog")]
        assert niveis and niveis[0] == 1
        assert soup.find_all("h1") and len([n for n in niveis if n == 1]) == 1
        for anterior, atual in zip(niveis, niveis[1:]):
            assert atual <= anterior + 1, f"salto de h{anterior} para h{atual}"


def test_link_pular_para_conteudo(paginas):
    for soup in paginas:
        primeiro_link = soup.body.find("a")
        assert primeiro_link["href"] == "#conteudo"
        assert soup.find(id="conteudo").name == "main"


def test_marcos_da_pagina(pagina):
    soup = pagina("/")
    assert soup.find("header") and soup.find("main") and soup.find("footer")
    nav = soup.select_one("nav.nav-categorias")
    assert nav["aria-label"]
    for link in nav.select("a"):
        assert soup.select_one(link["href"]), "âncora da categoria inexistente"


def test_pratos_agrupados_semanticamente(pagina):
    """Nome, preço e descrição ficam dentro de um <article> rotulado pelo nome."""
    soup = pagina("/")
    pratos = soup.select("article.prato")
    assert len(pratos) == 9
    for prato in pratos:
        titulo = soup.find(id=prato["aria-labelledby"])
        assert titulo.name in ("h2", "h3") and titulo.find_parent("article") is prato
        preco = prato.select_one(".prato-preco")
        assert preco.select_one(".apenas-leitor").get_text(strip=True) == "Preço:"
        assert preco.select_one("data[value]")
        assert prato.select_one(".prato-descricao").get_text(strip=True)
        # Cada prato é um item de lista, para o leitor anunciar "item X de Y".
        assert prato.parent.name == "li"


def test_ordem_do_dom_segue_a_leitura_do_card(pagina):
    prato = pagina("/").select_one("#prato-1")
    ordem = [el.get("class", [""])[0] or el.name for el in prato.find_all(recursive=False)]
    assert ordem == ["prato-cabecalho", "prato-foto", "prato-descricao", "prato-tags",
                     "prato-alergenos", "prato-ingredientes"]


def test_foto_preserva_descricao_e_botao_de_ampliar_tem_texto(pagina):
    prato = pagina("/").select_one("#prato-1")
    assert prato.img["alt"].startswith("Fatias de pão")
    botao = prato.select_one("[data-ampliar-foto]")
    assert botao.name == "button"
    assert botao.img is None  # a imagem não fica mais "escondida" dentro do botão
    assert nome_acessivel(botao) == "🔍 Ampliar foto : Bruschetta Clássica"


def test_emojis_decorativos_escondidos_do_leitor(pagina):
    soup = pagina("/")
    emoji = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
    for texto in soup.find_all(string=emoji):
        if texto.find_parent(["script", "style"]):
            continue
        assert texto.find_parent(attrs={"aria-hidden": "true"}), f"emoji exposto: {texto!r}"


def test_dialogo_da_foto_e_nativo(pagina):
    dialogo = pagina("/").select_one("dialog#dialogo-foto")
    assert dialogo["aria-labelledby"] == "dialogo-foto-titulo"
    assert dialogo.select_one("form[method=dialog] button")


def test_regiao_de_anuncios(pagina):
    regiao = pagina("/").select_one("#anuncios")
    assert regiao["role"] == "status" and regiao["aria-live"] == "polite"


def test_painel_de_acessibilidade_nativo_e_sem_toolbar(pagina):
    soup = pagina("/")
    assert soup.select_one("details#painel-acessibilidade > summary")
    # role=toolbar exige navegação por setas; não usamos.
    assert soup.select("[role=toolbar]") == []
    for fieldset in soup.select("#painel-acessibilidade fieldset"):
        assert fieldset.legend.get_text(strip=True)


def test_css_tem_indicador_de_foco_visivel():
    css = Path("app/static/css/style.css").read_text(encoding="utf-8")
    assert re.search(r":focus-visible\s*\{[^}]*outline:\s*3px", css)
    assert "outline: none" not in css.replace("main:focus { outline: none; }", "")
