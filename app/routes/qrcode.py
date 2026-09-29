"""QR Code que leva ao cardápio, para imprimir e colocar nas mesas."""

import io

import segno
from flask import Blueprint, Response, current_app, render_template, request, url_for

qrcode_bp = Blueprint("qrcode", __name__)

FORMATOS = {"svg": "image/svg+xml", "png": "image/png"}


def url_do_cardapio():
    base = current_app.config["PUBLIC_BASE_URL"]
    if base:
        return base.rstrip("/") + url_for("menu.index")
    return url_for("menu.index", _external=True)


@qrcode_bp.get("/qrcode")
def pagina():
    return render_template("qrcode.html", url_cardapio=url_do_cardapio())


@qrcode_bp.get("/qrcode.<formato>")
def imagem(formato):
    if formato not in FORMATOS:
        return Response(status=404)

    # Correção de erro "M" (~15%) tolera sujeira/desgaste de um QR impresso.
    qr = segno.make(url_do_cardapio(), error="m")
    buffer = io.BytesIO()
    escala = request.args.get("escala", default=10, type=int)
    escala = max(2, min(escala, 40))
    if formato == "svg":
        qr.save(buffer, kind="svg", scale=escala, border=4, xmldecl=False,
                title="QR Code do cardápio", svgclass=None, lineclass=None)
    else:
        qr.save(buffer, kind="png", scale=escala, border=4)

    resposta = Response(buffer.getvalue(), mimetype=FORMATOS[formato])
    if request.args.get("download"):
        resposta.headers["Content-Disposition"] = f'attachment; filename="cardapio-qrcode.{formato}"'
    resposta.cache_control.max_age = 3600
    return resposta
