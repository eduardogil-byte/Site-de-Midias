import secrets
from functools import wraps

from flask import abort, request, session

# sistema de segurança para evitar ataques CSRF (Cross-Site Request Forgery)
# impede que sites maliciosos enviem formulários fingindo ser o usuário logado


def gerar_csrf_token():
    # recupera ou cria senha temporária e única para a sessão do usuário
    token = session.get("csrf_token")

    if not token:
        token = secrets.token_urlsafe(32) # Gera um código aleatório criptograficamente seguro
        session["csrf_token"] = token

    return token


def validar_csrf():
    # compara o token que veio no formulário HTML com o token guardado na sessão
    token_formulario = request.form.get("csrf_token")
    token_sessao = session.get("csrf_token")

    if not token_formulario or not token_sessao:
        abort(400, description="Token CSRF ausente.") # interrompe e devolve erro

    # usando compare_digest no lugar de "==" para evitar "Timing Attacks" 
    # (ataques de hackers que tentam adivinhar a senha medindo os milissegundos da resposta do servidor)
    if not secrets.compare_digest(token_formulario, token_sessao):
        abort(400, description="Token CSRF invalido.")


def csrf_protect(view):
    # decorator que intercepta a requisição antes da função principal rodar
    @wraps(view)
    def wrapper(*args, **kwargs):
        # só exige o token de segurança se a requisição for POST
        if request.method == "POST":
            validar_csrf()

        # se é get ou passou pela verificcação, libera a rota para funcionar
        return view(*args, **kwargs)

    return wrapper