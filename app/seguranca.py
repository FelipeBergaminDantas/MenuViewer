"""Sessão do painel admin, proteção contra CSRF e redirecionamento seguro.

Sem dependências novas: a sessão assinada do Flask (cookie protegido pela
`SECRET_KEY`) guarda o id do usuário logado e um token CSRF aleatório, que todo
formulário POST do admin envia de volta num campo oculto.
"""

import hmac
import secrets
from urllib.parse import urlsplit

from flask import abort, request, session, url_for

from app.extensions import db
from app.models import Usuario

CHAVE_USUARIO = "usuario_id"
CHAVE_CSRF = "csrf"


def token_csrf():
    if CHAVE_CSRF not in session:
        session[CHAVE_CSRF] = secrets.token_urlsafe(32)
    return session[CHAVE_CSRF]


def validar_csrf():
    esperado = session.get(CHAVE_CSRF)
    recebido = request.form.get("csrf_token", "")
    if not esperado or not hmac.compare_digest(esperado, recebido):
        abort(400)


def autenticar(login, senha):
    """Devolve o usuário se login e senha conferem; senão, None."""
    usuario = db.session.execute(db.select(Usuario).filter_by(login=login)).scalar_one_or_none()
    if usuario and usuario.verificar_senha(senha):
        return usuario
    return None


def entrar(usuario):
    # Sessão nova a cada login: evita reaproveitar uma sessão criada antes (session fixation).
    session.clear()
    session[CHAVE_USUARIO] = usuario.id


def sair():
    session.clear()


def usuario_logado():
    usuario_id = session.get(CHAVE_USUARIO)
    return db.session.get(Usuario, usuario_id) if usuario_id else None


def destino_seguro(destino, padrao="menu.index"):
    """Aceita só caminhos relativos do próprio site (evita open redirect)."""
    if destino:
        partes = urlsplit(destino)
        if not partes.scheme and not partes.netloc and destino.startswith("/") and not destino.startswith("//"):
            return destino
    return url_for(padrao)
