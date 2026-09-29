"""Atualização das preferências de acessibilidade.

Um único endpoint atende os dois cenários:
- formulário HTML comum (sem JavaScript): responde com redirect de volta;
- `fetch` do JavaScript (Accept: application/json): responde com o novo estado,
  para a página aplicar a mudança sem recarregar.
O servidor é a única fonte de validação dos valores.
"""

from dataclasses import asdict
from urllib.parse import urlsplit

from flask import Blueprint, current_app, g, jsonify, redirect, request, url_for

from app.i18n import traduzir
from app.preferences import BOOLEANOS

preferencias_bp = Blueprint("preferencias", __name__)


@preferencias_bp.post("/preferencias")
def atualizar():
    novas = g.prefs.aplicar(
        request.form.get("acao", ""),
        request.form.get("valor"),
        idiomas=current_app.config["IDIOMAS"],
    )

    if request.accept_mimetypes.best == "application/json":
        resposta = jsonify(
            {
                **asdict(novas),
                "fonte_percentual": novas.fonte_percentual,
                "classes": novas.classes_html,
                "anuncio": _anuncio(novas),
            }
        )
    else:
        resposta = redirect(_destino_seguro(request.form.get("next")))

    config = current_app.config
    resposta.set_cookie(
        config["PREFS_COOKIE_NAME"],
        novas.to_cookie(),
        max_age=config["PREFS_COOKIE_MAX_AGE"],
        httponly=True,
        secure=config["PREFS_COOKIE_SECURE"],
        samesite="Lax",
    )
    return resposta


def _anuncio(prefs):
    """Mensagem curta para a região `aria-live`, confirmando a mudança."""
    acao = request.form.get("acao", "")
    if acao.startswith("fonte"):
        return traduzir("a11y.fonte_anuncio", n=prefs.fonte_percentual)
    if acao in BOOLEANOS:
        estado = "ativado" if getattr(prefs, acao) else "desativado"
        return traduzir(f"a11y.{acao}_{estado}")
    return ""


def _destino_seguro(destino):
    """Aceita só caminhos relativos do próprio site (evita open redirect)."""
    if destino:
        partes = urlsplit(destino)
        if not partes.scheme and not partes.netloc and destino.startswith("/") and not destino.startswith("//"):
            return destino
    return url_for("menu.index")
