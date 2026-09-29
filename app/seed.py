"""Dados de exemplo do cardápio.

Pratos referenciam ingredientes pelo nome; alérgenos e dietas são derivados
automaticamente (ver `app/models.py`).
"""

from decimal import Decimal

from app.extensions import db
from app.models import Alergeno, Categoria, Ingrediente, Origem, Prato

# Principais alérgenos (base: RDC 26/2015 da Anvisa, agrupados + gergelim).
# O nome exibido de cada código fica nas traduções: `alergeno.<codigo>`.
ALERGENOS = [
    "gluten",
    "leite",
    "ovo",
    "soja",
    "amendoim",
    "castanhas",
    "peixe",
    "crustaceos",
    "gergelim",
]

# nome: (origem, [alérgenos])
INGREDIENTES = {
    "pão italiano": (Origem.VEGETAL, ["gluten"]),
    "tomate": (Origem.VEGETAL, []),
    "alho": (Origem.VEGETAL, []),
    "manjericão": (Origem.VEGETAL, []),
    "azeite": (Origem.VEGETAL, []),
    "arroz arbóreo": (Origem.VEGETAL, []),
    "cogumelos": (Origem.VEGETAL, []),
    "manteiga": (Origem.ANIMAL, ["leite"]),
    "parmesão": (Origem.ANIMAL, ["leite"]),
    "grão-de-bico": (Origem.VEGETAL, []),
    "leite de coco": (Origem.VEGETAL, []),
    "pasta de curry vermelho": (Origem.VEGETAL, []),
    "pimenta": (Origem.VEGETAL, []),
    "arroz branco": (Origem.VEGETAL, []),
    "chocolate meio amargo": (Origem.ANIMAL, ["leite", "soja"]),
    "farinha de trigo": (Origem.VEGETAL, ["gluten"]),
    "ovos": (Origem.ANIMAL, ["ovo"]),
    "açúcar": (Origem.VEGETAL, []),
    "sorvete de creme": (Origem.ANIMAL, ["leite", "ovo"]),
    "laranja": (Origem.VEGETAL, []),
    "camarão": (Origem.CARNE, ["crustaceos"]),
    "salmão": (Origem.CARNE, ["peixe"]),
    "gergelim": (Origem.VEGETAL, ["gergelim"]),
    "molho shoyu": (Origem.VEGETAL, ["soja", "gluten"]),
    "folhas verdes": (Origem.VEGETAL, []),
    "castanha-de-caju": (Origem.VEGETAL, ["castanhas"]),
    "amendoim": (Origem.VEGETAL, ["amendoim"]),
    "limão": (Origem.VEGETAL, []),
    "hortelã": (Origem.VEGETAL, []),
}

CATEGORIAS = [
    ("Entradas", [
        {
            "nome": "Bruschetta Clássica",
            "descricao": "Pão italiano tostado com tomate, alho e manjericão fresco.",
            "preco": "22.00",
            "imagem": "bruschetta.jpg",
            "imagem_alt": "Fatias de pão tostado cobertas com tomate picado e folhas de manjericão.",
            "ingredientes": ["pão italiano", "tomate", "alho", "manjericão", "azeite"],
        },
        {
            "nome": "Salada de Folhas com Castanhas",
            "descricao": "Folhas verdes, castanha-de-caju tostada e molho de limão.",
            "preco": "26.00",
            "ingredientes": ["folhas verdes", "castanha-de-caju", "limão", "azeite"],
        },
    ]),
    ("Pratos Principais", [
        {
            "nome": "Risoto de Funghi",
            "descricao": "Arroz arbóreo cremoso com mix de cogumelos frescos e parmesão.",
            "preco": "48.00",
            "imagem": "risoto.jpg",
            "imagem_alt": "Prato de risoto cremoso com pedaços de cogumelo e queijo ralado por cima.",
            "ingredientes": ["arroz arbóreo", "cogumelos", "manteiga", "parmesão", "alho"],
        },
        {
            "nome": "Curry Picante de Grão-de-bico",
            "descricao": "Grão-de-bico ao molho de curry vermelho, leite de coco e pimenta.",
            "preco": "39.00",
            "imagem": "curry.jpg",
            "imagem_alt": "Tigela de curry alaranjado com grão-de-bico, servido com arroz branco ao lado.",
            "picante": True,
            "ingredientes": ["grão-de-bico", "leite de coco", "pasta de curry vermelho", "pimenta", "arroz branco"],
        },
        {
            "nome": "Salmão Grelhado com Gergelim",
            "descricao": "Salmão grelhado com crosta de gergelim e molho shoyu.",
            "preco": "62.00",
            "ingredientes": ["salmão", "gergelim", "molho shoyu", "arroz branco"],
        },
        {
            "nome": "Camarão ao Alho",
            "descricao": "Camarões salteados no azeite e alho, com arroz branco.",
            "preco": "58.00",
            "ingredientes": ["camarão", "alho", "azeite", "arroz branco"],
        },
    ]),
    ("Sobremesas", [
        {
            "nome": "Petit Gateau",
            "descricao": "Bolo de chocolate quente com recheio cremoso e sorvete de creme.",
            "preco": "28.00",
            "imagem": "petit_gateau.jpg",
            "imagem_alt": "Bolinho de chocolate partido ao meio com calda derretendo, ao lado de uma bola de sorvete.",
            "ingredientes": ["chocolate meio amargo", "farinha de trigo", "ovos", "manteiga", "açúcar", "sorvete de creme"],
        },
    ]),
    ("Bebidas", [
        {
            "nome": "Suco Natural de Laranja",
            "descricao": "Suco de laranja espremido na hora, sem açúcar adicionado.",
            "preco": "12.00",
            "imagem": "suco_laranja.jpg",
            "imagem_alt": "Copo de suco de laranja fresco em cima de uma mesa de madeira.",
            "ingredientes": ["laranja"],
        },
        {
            "nome": "Limonada com Hortelã",
            "descricao": "Limão espremido na hora com folhas de hortelã e açúcar.",
            "preco": "11.00",
            "ingredientes": ["limão", "hortelã", "açúcar"],
        },
    ]),
]


def seed_if_empty():
    """Popula o banco com os dados de exemplo se ainda estiver vazio."""
    if db.session.execute(db.select(Categoria.id).limit(1)).first():
        return False

    alergenos = {codigo: Alergeno(codigo=codigo, ordem=i) for i, codigo in enumerate(ALERGENOS)}
    ingredientes = {
        nome: Ingrediente(nome=nome, origem=origem, alergenos=[alergenos[a] for a in codigos])
        for nome, (origem, codigos) in INGREDIENTES.items()
    }
    db.session.add_all([*alergenos.values(), *ingredientes.values()])

    for ordem_cat, (nome_cat, pratos) in enumerate(CATEGORIAS, start=1):
        categoria = Categoria(nome=nome_cat, ordem=ordem_cat)
        for ordem_prato, dados in enumerate(pratos, start=1):
            dados = dict(dados)
            nomes = dados.pop("ingredientes")
            categoria.pratos.append(
                Prato(
                    **{**dados, "preco": Decimal(dados["preco"])},
                    ordem=ordem_prato,
                    ingredientes=[ingredientes[n] for n in nomes],
                )
            )
        db.session.add(categoria)

    db.session.commit()
    return True
