"""Critérios de aceite da issue "Modo de navegação simplificada"."""

from tests.conftest import nomes_dos_pratos


def ativar(client):
    return client.post("/preferencias", data={"acao": "simplificado", "next": "/"})


def test_opcao_disponivel_no_painel_de_acessibilidade(pagina):
    soup = pagina("/")
    botao = soup.select_one("#painel-acessibilidade button[value=simplificado]")
    assert botao.get_text(strip=True) == "Modo simplificado"
    assert botao["aria-pressed"] == "false"


def test_ativar_e_desativar(client, pagina):
    resposta = ativar(client)
    assert resposta.status_code == 302
    assert "simplificado=1" in resposta.headers["Set-Cookie"]

    soup = pagina("/")
    assert "modo-simplificado" in soup.html["class"]
    assert soup.select_one("#painel-acessibilidade button[value=simplificado]")["aria-pressed"] == "true"

    # Desativar de novo (pelo botão de saída, sempre visível no topo)
    sair = soup.select_one(".barra-simplificada button[value=simplificado]")
    assert sair.get_text(strip=True) == "Voltar ao modo completo"
    client.post("/preferencias", data={"acao": "simplificado", "next": "/"})
    soup = pagina("/")
    assert "modo-simplificado" not in soup.html.get("class", [])
    assert len(soup.select("section.categoria")) == 4


def test_exibe_uma_categoria_por_vez(client, pagina):
    ativar(client)
    soup = pagina("/")
    assert len(soup.select("section.categoria")) == 1
    assert soup.h1.get_text(strip=True) == "Entradas"
    assert nomes_dos_pratos(soup) == ["Bruschetta Clássica", "Salada de Folhas com Castanhas"]
    assert soup.select_one(".passo").get_text(strip=True) == "Categoria 1 de 4"


def test_navegacao_entre_categorias(client, pagina):
    ativar(client)
    soup = pagina("/")
    nav = soup.select_one("nav.nav-passos")
    assert nav["aria-label"]
    assert nav.select("a[rel=prev]") == []  # primeira categoria: sem "anterior"
    proxima = nav.select_one("a[rel=next]")
    assert "Próxima: Pratos Principais" in proxima.get_text(" ", strip=True)

    soup = pagina(proxima["href"])
    assert soup.h1.get_text(strip=True) == "Pratos Principais"
    assert soup.h1.has_attr("data-focar-ao-carregar")  # foco vai para o novo título
    assert "Anterior: Entradas" in soup.select_one("a[rel=prev]").get_text(" ", strip=True)
    assert "Pratos Principais (2/4)" in soup.title.text

    ultima = pagina(soup.select_one("a[rel=next]")["href"])
    ultima = pagina(ultima.select_one("a[rel=next]")["href"])
    assert ultima.h1.get_text(strip=True) == "Bebidas"
    assert ultima.select("a[rel=next]") == []


def test_categoria_invalida_volta_para_a_primeira(client, pagina):
    ativar(client)
    assert pagina("/?categoria=9999").h1.get_text(strip=True) == "Entradas"
    assert pagina("/?categoria=abc").h1.get_text(strip=True) == "Entradas"


def test_botoes_grandes_e_textos_curtos(client, pagina):
    ativar(client)
    soup = pagina("/")
    for link in soup.select("nav.nav-passos a"):
        assert "btn-grande" in link["class"]
        assert len(link.get_text(" ", strip=True).split()) <= 5


def test_reduz_elementos_visuais(client, pagina):
    ativar(client)
    soup = pagina("/")
    assert soup.select("nav.nav-categorias") == []
    assert soup.select("[data-ampliar-foto]") == []


def test_conteudo_dos_pratos_continua_disponivel(client, pagina):
    ativar(client)
    prato = pagina("/").select_one("article.prato")
    assert prato.h2.get_text(strip=True) == "Bruschetta Clássica"  # h1 = categoria
    assert prato.select_one(".prato-preco").get_text(" ", strip=True).endswith("R$ 22,00")
    assert "manjericão" in prato.select_one(".prato-descricao").text
    assert "glúten" in prato.select_one("[data-alergenos]").text
    assert "pão italiano" in prato.select_one("[data-ingredientes]").text
    assert prato.img["alt"]


def test_filtros_sao_preservados_na_navegacao(client, pagina):
    ativar(client)
    soup = pagina("/?dieta=vegano")
    proxima = soup.select_one("a[rel=next]")["href"]
    assert "dieta=vegano" in proxima
    soup = pagina(proxima)
    assert "Risoto de Funghi" not in nomes_dos_pratos(soup)
    # "Sobremesas" não tem prato vegano: pula direto de Principais para Bebidas
    assert "Bebidas" in soup.select_one("a[rel=next]").get_text()
