from decimal import Decimal

from tests.conftest import nomes_dos_pratos


def test_pagina_carrega_com_todas_as_categorias(pagina):
    soup = pagina("/")
    assert soup.h1.get_text(strip=True) == "Nosso cardápio"
    categorias = [h.get_text(strip=True) for h in soup.select("section.categoria h2")]
    assert categorias == ["Entradas", "Pratos Principais", "Sobremesas", "Bebidas"]
    assert len(nomes_dos_pratos(soup)) == 9


def test_preco_formatado_em_reais(pagina):
    soup = pagina("/")
    preco = soup.select_one("#prato-1 .prato-preco data")
    assert preco["value"] == "22.00"
    assert preco.get_text(strip=True) == "R$ 22,00"


def test_alergenos_derivados_dos_ingredientes(pagina):
    soup = pagina("/")
    petit = next(a for a in soup.select("article.prato") if "Petit Gateau" in a.h3.text)
    texto = petit.select_one("[data-alergenos]").get_text(" ", strip=True)
    for alergeno in ("glúten", "leite", "ovo", "soja"):
        assert alergeno in texto


def test_propriedades_derivadas_do_modelo(app):
    from app.extensions import db
    from app.models import Prato

    curry = db.session.execute(db.select(Prato).filter_by(nome="Curry Picante de Grão-de-bico")).scalar_one()
    risoto = db.session.execute(db.select(Prato).filter_by(nome="Risoto de Funghi")).scalar_one()
    camarao = db.session.execute(db.select(Prato).filter_by(nome="Camarão ao Alho")).scalar_one()

    assert curry.vegano and curry.vegetariano and curry.alergenos == []
    assert not risoto.vegano and risoto.vegetariano
    assert [a.codigo for a in risoto.alergenos] == ["leite"]
    assert not camarao.vegetariano
    assert isinstance(curry.preco, Decimal)


def test_link_para_qrcode_no_rodape(pagina):
    soup = pagina("/")
    assert soup.select_one("footer a[href='/qrcode']")
