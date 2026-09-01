from flask import Blueprint, render_template

from app.models import Categoria

menu_bp = Blueprint("menu", __name__)


@menu_bp.route("/")
def index():
    categorias = Categoria.query.order_by(Categoria.ordem).all()
    return render_template("menu.html", categorias=categorias)
