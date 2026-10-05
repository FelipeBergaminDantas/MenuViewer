"""Validação dos formulários do painel admin.

Cada `validar_*` recebe o formulário enviado e devolve `(dados, erros)`:
- `dados`: valores já convertidos, prontos para gravar no modelo;
- `erros`: {campo: chave de tradução da mensagem}. Vazio = formulário válido.

Os templates usam o mesmo nome de campo como `id` do input, então cada erro
pode apontar (com um link) para o campo que precisa ser corrigido.
"""

from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import current_app
from sqlalchemy import func

from app.extensions import db
from app.models import Alergeno, Categoria, Ingrediente, Origem

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
PRECO_MAXIMO = Decimal("99999999.99")  # limite de Numeric(10, 2)


def listar_imagens():
    """Fotos disponíveis em static/img/pratos (o upload ainda é manual)."""
    pasta = Path(current_app.static_folder) / "img" / "pratos"
    if not pasta.is_dir():
        return []
    return sorted(p.name for p in pasta.iterdir() if p.suffix.lower() in EXTENSOES_IMAGEM)


def validar_prato(form):
    erros = {}
    dados = {
        "nome": _texto(form, "nome", 120, erros, obrigatorio=True),
        "descricao": _texto(form, "descricao", 2000, erros),
        "preco": _preco(form, erros),
        "ordem": _inteiro(form, "ordem", erros),
        "picante": "picante" in form,
        "disponivel": "disponivel" in form,
        "imagem": form.get("imagem", "").strip() or None,
        "imagem_alt": _texto(form, "imagem_alt", 300, erros) or None,
    }

    categoria_id = form.get("categoria_id", type=int)
    dados["categoria"] = db.session.get(Categoria, categoria_id) if categoria_id else None
    if dados["categoria"] is None:
        erros["categoria_id"] = "admin.erros.categoria"

    ids = {int(i) for i in form.getlist("ingredientes") if i.isdigit()}
    dados["ingredientes"] = (
        db.session.execute(db.select(Ingrediente).where(Ingrediente.id.in_(ids))).scalars().all() if ids else []
    )

    if dados["imagem"] and dados["imagem"] not in listar_imagens():
        erros["imagem"] = "admin.erros.imagem"
    # Acessibilidade: toda foto publicada precisa de texto alternativo.
    if dados["imagem"] and not dados["imagem_alt"]:
        erros["imagem_alt"] = "admin.erros.imagem_alt"
    return dados, erros


def validar_categoria(form):
    erros = {}
    dados = {
        "nome": _texto(form, "nome", 80, erros, obrigatorio=True),
        "ordem": _inteiro(form, "ordem", erros),
    }
    return dados, erros


def validar_ingrediente(form, atual=None):
    erros = {}
    dados = {"nome": _texto(form, "nome", 120, erros, obrigatorio=True)}

    try:
        dados["origem"] = Origem(form.get("origem", ""))
    except ValueError:
        dados["origem"] = None
        erros["origem"] = "admin.erros.origem"

    codigos = form.getlist("alergenos")
    dados["alergenos"] = (
        db.session.execute(db.select(Alergeno).where(Alergeno.codigo.in_(codigos))).scalars().all()
        if codigos
        else []
    )

    if "nome" not in erros:
        consulta = db.select(Ingrediente.id).where(func.lower(Ingrediente.nome) == dados["nome"].lower())
        if atual is not None:
            consulta = consulta.where(Ingrediente.id != atual.id)
        if db.session.execute(consulta).first():
            erros["nome"] = "admin.erros.nome_repetido"
    return dados, erros


def aplicar(objeto, dados):
    for campo, valor in dados.items():
        setattr(objeto, campo, valor)


def _texto(form, campo, maximo, erros, obrigatorio=False):
    valor = form.get(campo, "").strip()
    if obrigatorio and not valor:
        erros[campo] = "admin.erros.obrigatorio"
    elif len(valor) > maximo:
        erros[campo] = "admin.erros.muito_longo"
    return valor


def _preco(form, erros):
    """Aceita "24,90", "24.90" e "1.234,50"."""
    texto = form.get("preco", "").strip().replace("R$", "").strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        valor = None
    if valor is None or not valor.is_finite() or not (0 <= valor <= PRECO_MAXIMO):
        erros["preco"] = "admin.erros.preco"
        return None
    return valor.quantize(Decimal("0.01"))


def _inteiro(form, campo, erros):
    texto = form.get(campo, "").strip()
    if not texto:
        return 0
    try:
        return int(texto)
    except ValueError:
        erros[campo] = "admin.erros.ordem"
        return 0
