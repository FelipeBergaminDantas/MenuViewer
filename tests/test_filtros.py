import pytest
from werkzeug.datastructures import MultiDict

from app.services.cardapio import FiltroCardapio, buscar_categorias
from tests.conftest import nomes_dos_pratos


def pratos_com(app, **args):
    filtro = FiltroCardapio.from_args(MultiDict(args), {
        "gluten", "leite", "ovo", "soja", "amendoim", "castanhas", "peixe", "crustaceos", "gergelim",
    })
    return {p.nome for c in buscar_categorias(filtro) for p in c.pratos}


def test_sem_filtro_mostra_tudo(app):
    assert len(pratos_com(app)) == 9


def test_filtro_vegano(app):
    assert pratos_com(app, dieta=["vegano"]) == {
        "Bruschetta Clássica",
        "Salada de Folhas com Castanhas",
        "Curry Picante de Grão-de-bico",
        "Suco Natural de Laranja",
        "Limonada com Hortelã",
    }


def test_filtro_vegetariano_exclui_carnes_mas_mantem_laticinios(app):
    pratos = pratos_com(app, dieta=["vegetariano"])
    assert "Risoto de Funghi" in pratos
    assert "Salmão Grelhado com Gergelim" not in pratos
    assert "Camarão ao Alho" not in pratos


def test_filtro_sem_picante(app):
    assert "Curry Picante de Grão-de-bico" not in pratos_com(app, dieta=["sem_picante"])


@pytest.mark.parametrize(
    "alergeno, excluidos",
    [
        ("gluten", {"Bruschetta Clássica", "Petit Gateau", "Salmão Grelhado com Gergelim"}),
        ("leite", {"Risoto de Funghi", "Petit Gateau"}),
        ("crustaceos", {"Camarão ao Alho"}),
        ("castanhas", {"Salada de Folhas com Castanhas"}),
        ("soja", {"Petit Gateau", "Salmão Grelhado com Gergelim"}),
    ],
)
def test_filtro_de_alergia_exclui_pratos_com_o_ingrediente(app, alergeno, excluidos):
    todos = pratos_com(app)
    assert pratos_com(app, sem=[alergeno]) == todos - excluidos


def test_filtros_combinados(app):
    assert pratos_com(app, dieta=["vegano", "sem_picante"], sem=["gluten", "castanhas"]) == {
        "Suco Natural de Laranja",
        "Limonada com Hortelã",
    }


def test_valores_desconhecidos_sao_ignorados(app):
    assert len(pratos_com(app, dieta=["carnivoro"], sem=["kriptonita"])) == 9


def test_categoria_sem_pratos_some(app):
    categorias = buscar_categorias(FiltroCardapio(dietas=frozenset({"vegano"})))
    assert "Sobremesas" not in [c.nome for c in categorias]


def test_prato_indisponivel_nao_aparece(app):
    from app.extensions import db
    from app.models import Prato

    suco = db.session.execute(db.select(Prato).filter_by(nome="Suco Natural de Laranja")).scalar_one()
    suco.disponivel = False
    db.session.commit()
    assert "Suco Natural de Laranja" not in pratos_com(app)


# ---------- Pela interface ----------

def test_formulario_de_filtro_usa_get_com_checkboxes_rotulados(pagina):
    soup = pagina("/")
    form = soup.select_one(".form-filtros")
    assert form["method"] == "get"
    checkboxes = form.select("input[type=checkbox]")
    assert {c["name"] for c in checkboxes} == {"dieta", "sem"}
    for checkbox in checkboxes:
        assert checkbox.find_parent("label"), "checkbox sem rótulo"
    # Agrupados por fieldset com legenda
    assert len(form.select("fieldset > legend")) == 2


def test_filtro_aplicado_pela_url(pagina):
    soup = pagina("/?sem=gluten&sem=leite&aplicado=1")
    nomes = nomes_dos_pratos(soup)
    assert "Bruschetta Clássica" not in nomes and "Risoto de Funghi" not in nomes
    assert soup.select_one("input[value=gluten]").has_attr("checked")
    assert soup.select_one(".painel-filtros").has_attr("open")

    resumo = soup.select_one("#resumo-filtro")
    assert resumo.has_attr("data-focar-ao-carregar")
    texto = resumo.get_text(" ", strip=True)
    assert "5 pratos encontrados" in texto
    assert "sem glúten" in texto


def test_estado_vazio(app, pagina):
    from app.extensions import db
    from app.models import Prato

    db.session.execute(db.update(Prato).values(disponivel=False))
    db.session.commit()
    soup = pagina("/")
    assert soup.select_one(".sem-resultados h2").get_text(strip=True) == "Nenhum prato encontrado"
    assert soup.select_one(".sem-resultados a[href='/']")
