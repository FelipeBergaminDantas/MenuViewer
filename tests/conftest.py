import pytest
from bs4 import BeautifulSoup

from app import create_app
from app.extensions import db as _db
from app.seed import seed_if_empty


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        seed_if_empty()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def pagina(client):
    """Faz GET e devolve o HTML já parseado."""

    def _pagina(url="/", **kwargs):
        resposta = client.get(url, **kwargs)
        assert resposta.status_code == 200, resposta.status_code
        return BeautifulSoup(resposta.data, "html.parser")

    return _pagina


@pytest.fixture
def definir_prefs(client):
    """Grava o cookie de preferências como o navegador faria."""

    def _definir(**prefs):
        from app.preferences import Preferencias

        client.set_cookie("prefs", Preferencias(**prefs).to_cookie())

    return _definir


def nomes_dos_pratos(soup):
    return [h.get_text(strip=True) for h in soup.select("article.prato .prato-nome")]
