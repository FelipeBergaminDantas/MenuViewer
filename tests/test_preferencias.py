import pytest

from app.preferences import FONTE_MAX, FONTE_MIN, Preferencias

IDIOMAS = ("pt", "en", "es")


def test_cookie_ida_e_volta():
    prefs = Preferencias(fonte=1.3, contraste=True, simplificado=True, idioma="en")
    assert Preferencias.from_cookie(prefs.to_cookie(), IDIOMAS) == prefs


@pytest.mark.parametrize("cookie", ["", "lixo", "fonte=abc", "fonte=99&idioma=klingon", "%%%", "contraste=talvez"])
def test_cookie_invalido_nao_quebra(cookie):
    prefs = Preferencias.from_cookie(cookie, IDIOMAS)
    assert FONTE_MIN <= prefs.fonte <= FONTE_MAX
    assert prefs.idioma in ("", *IDIOMAS)


def test_fonte_respeita_limites():
    prefs = Preferencias()
    for _ in range(30):
        prefs = prefs.aplicar("fonte_mais")
    assert prefs.fonte == FONTE_MAX
    for _ in range(30):
        prefs = prefs.aplicar("fonte_menos")
    assert prefs.fonte == FONTE_MIN
    assert prefs.aplicar("fonte_padrao").fonte == 1.0


def test_aumentar_fonte_pelo_formulario(client, pagina):
    client.post("/preferencias", data={"acao": "fonte_mais"})
    client.post("/preferencias", data={"acao": "fonte_mais"})
    soup = pagina("/")
    assert "--escala-fonte: 1.2" in soup.html["style"]
    assert soup.select_one("[data-saida-fonte]").get_text(strip=True) == "120%"


def test_resposta_json_para_o_javascript(client):
    resposta = client.post(
        "/preferencias", data={"acao": "contraste"}, headers={"Accept": "application/json"}
    )
    assert resposta.is_json
    assert resposta.json["contraste"] is True
    assert resposta.json["classes"] == "alto-contraste"
    assert resposta.json["anuncio"] == "Alto contraste ativado"
    cookie = resposta.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie


def test_estado_renderizado_no_servidor(client, pagina, definir_prefs):
    definir_prefs(contraste=True, movimento_reduzido=True)
    soup = pagina("/")
    assert {"alto-contraste", "movimento-reduzido"} <= set(soup.html["class"])
    painel = soup.select_one("#painel-acessibilidade")
    assert painel.select_one("button[value=contraste]")["aria-pressed"] == "true"
    assert painel.select_one("button[value=movimento_reduzido]")["aria-pressed"] == "true"


@pytest.mark.parametrize("destino", ["https://malicioso.com", "//malicioso.com", "javascript:alert(1)", ""])
def test_redirect_seguro(client, destino):
    resposta = client.post("/preferencias", data={"acao": "contraste", "next": destino})
    assert resposta.headers["Location"] == "/"


def test_redirect_volta_para_a_pagina_de_origem(client):
    resposta = client.post("/preferencias", data={"acao": "contraste", "next": "/?dieta=vegano"})
    assert resposta.headers["Location"] == "/?dieta=vegano"


def test_trocar_idioma(client, pagina):
    client.post("/preferencias", data={"acao": "idioma", "valor": "en"})
    soup = pagina("/")
    assert soup.html["lang"] == "en"
    assert soup.h1.get_text(strip=True) == "Our menu"
    assert soup.select_one("button[value=en]")["aria-pressed"] == "true"
    assert soup.select_one("#prato-1 .prato-preco data").get_text(strip=True) == "R$22.00"


def test_idioma_detectado_pelo_navegador(pagina):
    soup = pagina("/", headers={"Accept-Language": "es-ES,es;q=0.9"})
    assert soup.html["lang"] == "es"
    assert soup.h1.get_text(strip=True) == "Nuestro menú"
