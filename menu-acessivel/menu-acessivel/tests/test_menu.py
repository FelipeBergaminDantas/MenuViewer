import pytest

from app import create_app
from app.database import db


@pytest.fixture
def client():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    with app.test_client() as client:
        yield client


def test_menu_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Cardápio".encode("utf-8") in response.data or b"Cardapio" in response.data


def test_menu_shows_seeded_categories(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Entradas".encode("utf-8") in response.data
