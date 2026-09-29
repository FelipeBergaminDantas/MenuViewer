from flask import Blueprint, g, render_template, request

from app.services.cardapio import (
    DIETAS,
    FiltroCardapio,
    buscar_categorias,
    contar_pratos,
    listar_alergenos,
)

menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/")
def index():
    alergenos = listar_alergenos()
    filtro = FiltroCardapio.from_args(request.args, {a.codigo for a in alergenos})
    categorias = buscar_categorias(filtro)

    contexto = {
        "categorias": categorias,
        "total_pratos": contar_pratos(categorias),
        "filtro": filtro,
        "dietas": DIETAS,
        "alergenos": alergenos,
    }

    if g.prefs.simplificado:
        return render_template("menu_simplificado.html", **contexto, **_passo_atual(categorias))
    return render_template("menu.html", **contexto)


def _passo_atual(categorias):
    """No modo simplificado, qual categoria mostrar e quais são as vizinhas."""
    if not categorias:
        return {"atual": None, "indice": 0, "anterior": None, "proxima": None}

    categoria_id = request.args.get("categoria", type=int)
    indice = next((i for i, c in enumerate(categorias) if c.id == categoria_id), 0)
    return {
        "atual": categorias[indice],
        "indice": indice,
        "anterior": categorias[indice - 1] if indice > 0 else None,
        "proxima": categorias[indice + 1] if indice + 1 < len(categorias) else None,
    }
