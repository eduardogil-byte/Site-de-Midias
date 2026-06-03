import secrets
from functools import wraps

from flask import abort, request, session


def gerar_csrf_token():
    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token

    return token


def validar_csrf():
    token_formulario = request.form.get("csrf_token")
    token_sessao = session.get("csrf_token")

    if not token_formulario or not token_sessao:
        abort(400, description="Token CSRF ausente.")

    if not secrets.compare_digest(token_formulario, token_sessao):
        abort(400, description="Token CSRF invalido.")


def csrf_protect(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            validar_csrf()

        return view(*args, **kwargs)

    return wrapper
