"""Regras de consulta do cardápio (filtros alimentares e de alergias).

Os filtros são aplicados no banco (SQL), não em Python, para que continuem
eficientes com cardápios grandes. As rotas só traduzem a requisição em um
`FiltroCardapio` e chamam `buscar_categorias`.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import contains_eager

from app.extensions import db
from app.models import Alergeno, Categoria, Ingrediente, Origem, Prato

DIETAS = ("vegano", "vegetariano", "sem_picante")


@dataclass(frozen=True)
class FiltroCardapio:
    dietas: frozenset = field(default_factory=frozenset)
    excluir_alergenos: frozenset = field(default_factory=frozenset)

    @classmethod
    def from_args(cls, args, codigos_validos):
        """Monta o filtro a partir da query string, descartando valores desconhecidos.

        Formato: `?dieta=vegano&dieta=sem_picante&sem=gluten&sem=leite`
        """
        dietas = frozenset(d for d in args.getlist("dieta") if d in DIETAS)
        alergenos = frozenset(a for a in args.getlist("sem") if a in codigos_validos)
        return cls(dietas=dietas, excluir_alergenos=alergenos)

    @property
    def ativo(self):
        return bool(self.dietas or self.excluir_alergenos)

    def to_args(self):
        """Parâmetros de URL equivalentes, para preservar o filtro em links."""
        return {"dieta": sorted(self.dietas), "sem": sorted(self.excluir_alergenos)}


def condicoes_do_filtro(filtro):
    """Lista de expressões SQL que um prato precisa satisfazer."""
    condicoes = [Prato.disponivel.is_(True)]

    if "vegano" in filtro.dietas:
        condicoes.append(~Prato.ingredientes.any(Ingrediente.origem != Origem.VEGETAL))
        condicoes.append(Prato.ingredientes.any())  # sem ingredientes cadastrados = desconhecido
    if "vegetariano" in filtro.dietas:
        condicoes.append(~Prato.ingredientes.any(Ingrediente.origem == Origem.CARNE))
        condicoes.append(Prato.ingredientes.any())
    if "sem_picante" in filtro.dietas:
        condicoes.append(Prato.picante.is_(False))
    if filtro.excluir_alergenos:
        condicoes.append(
            ~Prato.ingredientes.any(
                Ingrediente.alergenos.any(Alergeno.codigo.in_(filtro.excluir_alergenos))
            )
        )
    return condicoes


def buscar_categorias(filtro=None):
    """Categorias com seus pratos já filtrados, em ordem.

    Categorias que ficam sem nenhum prato após o filtro são omitidas.
    """
    filtro = filtro or FiltroCardapio()
    consulta = (
        db.select(Categoria)
        .join(Categoria.pratos)
        .where(*condicoes_do_filtro(filtro))
        .options(contains_eager(Categoria.pratos))
        .order_by(Categoria.ordem, Categoria.id, Prato.ordem, Prato.id)
        # Garante que a coleção `pratos` reflita este filtro, mesmo que a
        # categoria já tenha sido carregada antes na mesma sessão.
        .execution_options(populate_existing=True)
    )
    return db.session.execute(consulta).unique().scalars().all()


def contar_pratos(categorias):
    return sum(len(c.pratos) for c in categorias)


def listar_alergenos():
    return db.session.execute(db.select(Alergeno).order_by(Alergeno.ordem)).scalars().all()
