from decimal import Decimal

import pytest
from bs4 import BeautifulSoup

from app.extensions import db
from app.models import Categoria, Ingrediente, Prato, Usuario, prato_ingrediente
from tests.conftest import nomes_dos_pratos

CSRF = "token-de-teste"


@pytest.fixture
def usuario(app):
    usuario = Usuario(login="equipe")
    usuario.definir_senha("senha-forte-123")
    db.session.add(usuario)
    db.session.commit()
    return usuario


@pytest.fixture
def admin(client, usuario):
    """Cliente já logado, com token CSRF conhecido na sessão."""
    with client.session_transaction() as sessao:
        sessao["usuario_id"] = usuario.id
        sessao["csrf"] = CSRF
    return client


def postar(client, url, **dados):
    return client.post(url, data={"csrf_token": CSRF, **dados})


def buscar(modelo, **filtro):
    return db.session.execute(db.select(modelo).filter_by(**filtro)).scalar_one_or_none()


# ---------- Login e segurança ----------


@pytest.mark.parametrize("url", ["/admin/pratos", "/admin/categorias/nova", "/admin/ingredientes"])
def test_paginas_exigem_login(client, url):
    resposta = client.get(url)
    assert resposta.status_code == 302
    assert resposta.location.startswith("/admin/login?next=")


def test_login_e_logout(client, usuario):
    soup = BeautifulSoup(client.get("/admin/login?next=/admin/ingredientes").data, "html.parser")
    token = soup.select_one("input[name=csrf_token]")["value"]

    errado = client.post("/admin/login", data={"csrf_token": token, "login": "equipe", "senha": "x"})
    assert "Usuário ou senha incorretos" in errado.get_data(as_text=True)

    certo = client.post("/admin/login", data={
        "csrf_token": token, "login": "equipe", "senha": "senha-forte-123", "next": "/admin/ingredientes",
    })
    assert certo.status_code == 302 and certo.location == "/admin/ingredientes"
    assert client.get("/admin/pratos").status_code == 200

    # O login gera uma sessão nova: o token antigo deixa de valer.
    with client.session_transaction() as sessao:
        sessao["csrf"] = CSRF
    assert postar(client, "/admin/sair").status_code == 302
    assert client.get("/admin/pratos").status_code == 302


def test_login_nao_redireciona_para_outro_site(client, usuario):
    with client.session_transaction() as sessao:
        sessao["csrf"] = CSRF
    resposta = postar(client, "/admin/login", login="equipe", senha="senha-forte-123", next="//site-malicioso.com")
    assert resposta.location == "/admin/pratos"


def test_post_sem_token_csrf_e_recusado(admin):
    resposta = admin.post("/admin/categorias/nova", data={"nome": "Petiscos"})
    assert resposta.status_code == 400
    assert buscar(Categoria, nome="Petiscos") is None


def test_paginas_do_admin_nao_ficam_em_cache(admin):
    assert admin.get("/admin/pratos").headers["Cache-Control"] == "no-store"


# ---------- Pratos ----------


def test_criar_prato_aparece_no_cardapio(admin, pagina):
    bebidas = buscar(Categoria, nome="Bebidas")
    laranja = buscar(Ingrediente, nome="laranja")
    resposta = postar(admin, "/admin/pratos/novo", nome="Suco Verde", descricao="Couve e laranja.",
                      preco="14,50", categoria_id=bebidas.id, ingredientes=[laranja.id], disponivel="1")
    assert resposta.status_code == 302

    prato = buscar(Prato, nome="Suco Verde")
    assert prato.preco == Decimal("14.50") and prato.vegano
    assert "Suco Verde" in nomes_dos_pratos(pagina("/"))


def test_formulario_invalido_mostra_erros_acessiveis(admin):
    resposta = postar(admin, "/admin/pratos/novo", nome="", preco="abc", imagem="risoto.jpg", imagem_alt="")
    assert resposta.status_code == 422
    soup = BeautifulSoup(resposta.data, "html.parser")

    links = {a["href"] for a in soup.select(".resumo-erros a")}
    assert {"#nome", "#preco", "#categoria_id", "#imagem_alt"} <= links
    preco = soup.select_one("#preco")
    assert preco["aria-invalid"] == "true"
    assert "preco-erro" in preco["aria-describedby"]
    assert preco["value"] == "abc"  # o que a pessoa digitou não se perde


def test_prato_indisponivel_some_do_cardapio(admin, pagina):
    risoto = buscar(Prato, nome="Risoto de Funghi")
    postar(admin, f"/admin/pratos/{risoto.id}/editar", nome=risoto.nome, preco="48",
           categoria_id=risoto.categoria_id, ingredientes=[i.id for i in risoto.ingredientes])
    assert "Risoto de Funghi" not in nomes_dos_pratos(pagina("/"))
    assert "Indisponível" in admin.get("/admin/pratos").get_data(as_text=True)


def test_excluir_prato_pede_confirmacao(admin):
    curry = buscar(Prato, nome="Curry Picante de Grão-de-bico")
    assert admin.get(f"/admin/pratos/{curry.id}/excluir").status_code == 200
    assert buscar(Prato, id=curry.id) is not None

    postar(admin, f"/admin/pratos/{curry.id}/excluir")
    assert buscar(Prato, id=curry.id) is None


# ---------- Categorias ----------


def test_categoria_com_pratos_nao_pode_ser_excluida(admin):
    entradas = buscar(Categoria, nome="Entradas")
    resposta = postar(admin, f"/admin/categorias/{entradas.id}/excluir")
    assert resposta.status_code == 409
    assert buscar(Categoria, nome="Entradas") is not None


def test_criar_e_excluir_categoria_vazia(admin):
    postar(admin, "/admin/categorias/nova", nome="Petiscos", ordem="5")
    petiscos = buscar(Categoria, nome="Petiscos")
    assert petiscos.ordem == 5
    postar(admin, f"/admin/categorias/{petiscos.id}/excluir")
    assert buscar(Categoria, nome="Petiscos") is None


# ---------- Ingredientes ----------


def test_alergeno_do_ingrediente_muda_o_filtro_dos_pratos(admin, pagina):
    """Alérgenos são derivados: editar o ingrediente atualiza todos os pratos que o usam."""
    tomate = buscar(Ingrediente, nome="tomate")
    postar(admin, f"/admin/ingredientes/{tomate.id}/editar", nome="tomate", origem="vegetal", alergenos=["gluten"])
    assert "Bruschetta Clássica" not in nomes_dos_pratos(pagina("/?sem=gluten"))

    laranja = buscar(Ingrediente, nome="laranja")
    postar(admin, f"/admin/ingredientes/{laranja.id}/editar", nome="laranja", origem="vegetal", alergenos=["gluten"])
    assert "Suco Natural de Laranja" not in nomes_dos_pratos(pagina("/?sem=gluten"))


def test_nome_de_ingrediente_repetido(admin):
    resposta = postar(admin, "/admin/ingredientes/novo", nome="Tomate", origem="vegetal")
    assert resposta.status_code == 422
    assert "Já existe um ingrediente" in resposta.get_data(as_text=True)


def test_excluir_ingrediente_remove_dos_pratos(admin):
    alho = buscar(Ingrediente, nome="alho")
    pagina_confirmacao = admin.get(f"/admin/ingredientes/{alho.id}/excluir").get_data(as_text=True)
    assert "Camarão ao Alho" in pagina_confirmacao  # avisa quais pratos serão afetados

    postar(admin, f"/admin/ingredientes/{alho.id}/excluir")
    # Sem linhas órfãs: um ingrediente novo que reaproveite o id não "entra" em pratos antigos.
    restantes = db.session.execute(
        db.select(prato_ingrediente).where(prato_ingrediente.c.ingrediente_id == alho.id)
    ).all()
    assert restantes == []


# ---------- Linha de comando e configuração ----------


def test_comando_criar_admin(app):
    runner = app.test_cli_runner()
    resultado = runner.invoke(args=["criar-admin", "gerente", "--senha", "senha-forte-123"])
    assert "criado" in resultado.output
    assert buscar(Usuario, login="gerente").verificar_senha("senha-forte-123")

    curta = runner.invoke(args=["criar-admin", "gerente", "--senha", "123"])
    assert curta.exit_code != 0


def test_producao_exige_secret_key(monkeypatch):
    from app import create_app
    from app.config import SECRET_KEY_DEV, ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", SECRET_KEY_DEV)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")
