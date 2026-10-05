"""Painel admin: a equipe do restaurante cadastra pratos, categorias e ingredientes.

Tudo em /admin exige login. Os formulários são HTML comum (funcionam sem
JavaScript) e todo POST leva um token CSRF, conferido antes de qualquer outra coisa.
Excluir algo sempre passa por uma página de confirmação (GET mostra, POST exclui).
"""

from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func

from app.extensions import db
from app.i18n import traduzir
from app.models import Alergeno, Categoria, Ingrediente, Origem, Prato
from app.seguranca import (
    autenticar,
    destino_seguro,
    entrar,
    sair,
    token_csrf,
    usuario_logado,
    validar_csrf,
)
from app.services.admin import (
    aplicar,
    listar_imagens,
    validar_categoria,
    validar_ingrediente,
    validar_prato,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.before_request
def exigir_login():
    if request.method == "POST":
        validar_csrf()
    g.usuario = usuario_logado()
    if g.usuario is None and request.endpoint != "admin.login":
        return redirect(url_for("admin.login", next=request.full_path.rstrip("?")))
    return None


@admin_bp.after_request
def sem_cache(resposta):
    # Páginas do admin não devem ficar no cache (ex.: botão "voltar" após sair).
    resposta.headers["Cache-Control"] = "no-store"
    return resposta


@admin_bp.context_processor
def injetar_globais_admin():
    return {"csrf_token": token_csrf, "usuario": g.get("usuario")}


# ---------- Login ----------


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("admin.pratos"))

    erro = None
    if request.method == "POST":
        usuario = autenticar(request.form.get("login", "").strip(), request.form.get("senha", ""))
        if usuario:
            entrar(usuario)
            return redirect(destino_seguro(request.form.get("next"), padrao="admin.pratos"))
        erro = "admin.login.erro"
    return render_template("admin/login.html", erro=erro, proximo=request.values.get("next", ""))


@admin_bp.post("/sair")
def logout():
    sair()
    flash(traduzir("admin.login.saiu"), "sucesso")
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
def inicio():
    return redirect(url_for("admin.pratos"))


# ---------- Pratos ----------


@admin_bp.get("/pratos")
def pratos():
    categorias = db.session.execute(db.select(Categoria).order_by(Categoria.ordem, Categoria.id)).scalars().all()
    return render_template("admin/pratos.html", categorias=categorias)


@admin_bp.route("/pratos/novo", methods=["GET", "POST"])
def novo_prato():
    return _formulario_prato(None)


@admin_bp.route("/pratos/<int:prato_id>/editar", methods=["GET", "POST"])
def editar_prato(prato_id):
    return _formulario_prato(_buscar(Prato, prato_id))


def _formulario_prato(prato):
    erros = {}
    if request.method == "POST":
        dados, erros = validar_prato(request.form)
        if not erros:
            if prato is None:
                prato = Prato()
                db.session.add(prato)
            aplicar(prato, dados)
            db.session.commit()
            flash(traduzir("admin.salvo", nome=prato.nome), "sucesso")
            return redirect(url_for("admin.pratos"))
        valores = _valores_do_form(request.form, listas=("ingredientes",))
    else:
        valores = _valores_prato(prato)

    return render_template(
        "admin/prato_form.html",
        prato=prato,
        valores=valores,
        erros=erros,
        categorias=db.session.execute(db.select(Categoria).order_by(Categoria.ordem)).scalars().all(),
        ingredientes=db.session.execute(db.select(Ingrediente).order_by(Ingrediente.nome)).scalars().all(),
        imagens=listar_imagens(),
    ), (422 if erros else 200)


def _valores_prato(prato):
    if prato is None:
        proxima_ordem = (db.session.scalar(db.select(func.max(Prato.ordem))) or 0) + 1
        return {"ordem": str(proxima_ordem), "disponivel": "1", "ingredientes": []}
    return {
        "nome": prato.nome,
        "descricao": prato.descricao,
        "preco": str(prato.preco),
        "categoria_id": str(prato.categoria_id),
        "ordem": str(prato.ordem),
        "imagem": prato.imagem or "",
        "imagem_alt": prato.imagem_alt or "",
        "picante": "1" if prato.picante else "",
        "disponivel": "1" if prato.disponivel else "",
        "ingredientes": [str(i.id) for i in prato.ingredientes],
    }


@admin_bp.route("/pratos/<int:prato_id>/excluir", methods=["GET", "POST"])
def excluir_prato(prato_id):
    prato = _buscar(Prato, prato_id)
    if request.method == "POST":
        db.session.delete(prato)
        db.session.commit()
        flash(traduzir("admin.excluido", nome=prato.nome), "sucesso")
        return redirect(url_for("admin.pratos"))
    return render_template("admin/excluir.html", nome=prato.nome, voltar=url_for("admin.pratos"),
                           dica=traduzir("admin.pratos.excluir_dica"))


# ---------- Categorias ----------


@admin_bp.get("/categorias")
def categorias():
    lista = db.session.execute(db.select(Categoria).order_by(Categoria.ordem, Categoria.id)).scalars().all()
    return render_template("admin/categorias.html", categorias=lista)


@admin_bp.route("/categorias/nova", methods=["GET", "POST"])
def nova_categoria():
    return _formulario_categoria(None)


@admin_bp.route("/categorias/<int:categoria_id>/editar", methods=["GET", "POST"])
def editar_categoria(categoria_id):
    return _formulario_categoria(_buscar(Categoria, categoria_id))


def _formulario_categoria(categoria):
    erros = {}
    if request.method == "POST":
        dados, erros = validar_categoria(request.form)
        if not erros:
            if categoria is None:
                categoria = Categoria()
                db.session.add(categoria)
            aplicar(categoria, dados)
            db.session.commit()
            flash(traduzir("admin.salvo", nome=categoria.nome), "sucesso")
            return redirect(url_for("admin.categorias"))
        valores = _valores_do_form(request.form)
    elif categoria is None:
        proxima_ordem = (db.session.scalar(db.select(func.max(Categoria.ordem))) or 0) + 1
        valores = {"ordem": str(proxima_ordem)}
    else:
        valores = {"nome": categoria.nome, "ordem": str(categoria.ordem)}

    return render_template(
        "admin/categoria_form.html", categoria=categoria, valores=valores, erros=erros
    ), (422 if erros else 200)


@admin_bp.route("/categorias/<int:categoria_id>/excluir", methods=["GET", "POST"])
def excluir_categoria(categoria_id):
    categoria = _buscar(Categoria, categoria_id)
    # Não exclui categoria com pratos: os pratos ficariam sem categoria.
    bloqueio = traduzir("admin.categorias.excluir_bloqueado", n=len(categoria.pratos)) if categoria.pratos else None
    if request.method == "POST" and not bloqueio:
        db.session.delete(categoria)
        db.session.commit()
        flash(traduzir("admin.excluido", nome=categoria.nome), "sucesso")
        return redirect(url_for("admin.categorias"))
    return render_template("admin/excluir.html", nome=categoria.nome, voltar=url_for("admin.categorias"),
                           bloqueio=bloqueio), (409 if bloqueio and request.method == "POST" else 200)


# ---------- Ingredientes ----------


@admin_bp.get("/ingredientes")
def ingredientes():
    lista = db.session.execute(db.select(Ingrediente).order_by(Ingrediente.nome)).scalars().all()
    return render_template("admin/ingredientes.html", ingredientes=lista)


@admin_bp.route("/ingredientes/novo", methods=["GET", "POST"])
def novo_ingrediente():
    return _formulario_ingrediente(None)


@admin_bp.route("/ingredientes/<int:ingrediente_id>/editar", methods=["GET", "POST"])
def editar_ingrediente(ingrediente_id):
    return _formulario_ingrediente(_buscar(Ingrediente, ingrediente_id))


def _formulario_ingrediente(ingrediente):
    erros = {}
    if request.method == "POST":
        dados, erros = validar_ingrediente(request.form, atual=ingrediente)
        if not erros:
            if ingrediente is None:
                ingrediente = Ingrediente()
                db.session.add(ingrediente)
            aplicar(ingrediente, dados)
            db.session.commit()
            flash(traduzir("admin.salvo", nome=ingrediente.nome), "sucesso")
            return redirect(url_for("admin.ingredientes"))
        valores = _valores_do_form(request.form, listas=("alergenos",))
    elif ingrediente is None:
        valores = {"origem": Origem.VEGETAL.value, "alergenos": []}
    else:
        valores = {
            "nome": ingrediente.nome,
            "origem": ingrediente.origem.value,
            "alergenos": [a.codigo for a in ingrediente.alergenos],
        }

    return render_template(
        "admin/ingrediente_form.html",
        ingrediente=ingrediente,
        valores=valores,
        erros=erros,
        origens=list(Origem),
        alergenos=db.session.execute(db.select(Alergeno).order_by(Alergeno.ordem)).scalars().all(),
    ), (422 if erros else 200)


@admin_bp.route("/ingredientes/<int:ingrediente_id>/excluir", methods=["GET", "POST"])
def excluir_ingrediente(ingrediente_id):
    ingrediente = _buscar(Ingrediente, ingrediente_id)
    if request.method == "POST":
        db.session.delete(ingrediente)
        db.session.commit()
        flash(traduzir("admin.excluido", nome=ingrediente.nome), "sucesso")
        return redirect(url_for("admin.ingredientes"))
    return render_template("admin/excluir.html", nome=ingrediente.nome, voltar=url_for("admin.ingredientes"),
                           afetados=[p.nome for p in ingrediente.pratos])


# ---------- Auxiliares ----------


def _buscar(modelo, objeto_id):
    objeto = db.session.get(modelo, objeto_id)
    if objeto is None:
        abort(404)
    return objeto


def _valores_do_form(form, listas=()):
    """Reexibe o que a pessoa digitou quando o formulário volta com erros."""
    valores = form.to_dict()
    for campo in listas:
        valores[campo] = form.getlist(campo)
    return valores
