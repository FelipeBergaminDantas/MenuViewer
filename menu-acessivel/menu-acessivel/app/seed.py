from app.database import db
from app.models import Categoria, Prato


def seed_if_empty():
    """Popula o banco com dados de exemplo se ainda estiver vazio."""
    if Categoria.query.first():
        return

    entradas = Categoria(nome="Entradas", ordem=1)
    principais = Categoria(nome="Pratos Principais", ordem=2)
    sobremesas = Categoria(nome="Sobremesas", ordem=3)
    bebidas = Categoria(nome="Bebidas", ordem=4)

    db.session.add_all([entradas, principais, sobremesas, bebidas])
    db.session.flush()

    pratos = [
        Prato(
            nome="Bruschetta Clássica",
            descricao="Pão italiano tostado com tomate, alho e manjericão fresco.",
            preco=22.00,
            imagem="bruschetta.jpg",
            imagem_alt="Fatias de pão tostado cobertas com tomate picado e folhas de manjericão.",
            vegano=True,
            categoria_id=entradas.id,
        ),
        Prato(
            nome="Risoto de Funghi",
            descricao="Arroz arbóreo cremoso com mix de cogumelos frescos e parmesão.",
            preco=48.00,
            imagem="risoto.jpg",
            imagem_alt="Prato de risoto cremoso com pedaços de cogumelo e queijo ralado por cima.",
            sem_gluten=True,
            categoria_id=principais.id,
        ),
        Prato(
            nome="Curry Picante de Grão-de-bico",
            descricao="Grão-de-bico ao molho de curry vermelho, leite de coco e pimenta.",
            preco=39.00,
            imagem="curry.jpg",
            imagem_alt="Tigela de curry alaranjado com grão-de-bico, servido com arroz branco ao lado.",
            vegano=True,
            sem_gluten=True,
            picante=True,
            categoria_id=principais.id,
        ),
        Prato(
            nome="Petit Gateau",
            descricao="Bolo de chocolate quente com recheio cremoso e sorvete de creme.",
            preco=28.00,
            imagem="petit_gateau.jpg",
            imagem_alt="Bolinho de chocolate partido ao meio com calda derretendo, ao lado de uma bola de sorvete.",
            categoria_id=sobremesas.id,
        ),
        Prato(
            nome="Suco Natural de Laranja",
            descricao="Suco de laranja espremido na hora, sem açúcar adicionado.",
            preco=12.00,
            imagem="suco_laranja.jpg",
            imagem_alt="Copo de suco de laranja fresco em cima de uma mesa de madeira.",
            vegano=True,
            sem_gluten=True,
            categoria_id=bebidas.id,
        ),
    ]

    db.session.add_all(pratos)
    db.session.commit()
