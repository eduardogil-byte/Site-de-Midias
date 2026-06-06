from flask import Flask
from flask_jwt_extended import JWTManager # biblioteca para autenticar com tokens
import os

from app.database import db
from app.security import gerar_csrf_token

template_dir = os.path.abspath("app/views/templates") # caminho dos arquivos HTML
static_dir = os.path.abspath("app/static") # caminho dos arquivos estáticos

# inicialização do app
app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)



# (1) CONFIGURAÇÕES DA APLICAÇÃO E SEGURANÇA

# chave secreta geral do Flask, se os cookies forem alterados bloqueia o acesso à conta
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "midiahub-chave-de-desenvolvimento-com-mais-de-32-bytes", # nome temporário para os testes
)

# chave secreta específica para o JWT (se tentar alterar o token o acesso vai falhar por não ter a senha)
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    "midiahub-chave-jwt-de-desenvolvimento-com-mais-de-32-bytes",
)

# configuração do SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///midiahub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# proteções extras para ataques
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # limita uploads a 16MB, evitando ataques de negação de serviço (DoS)
app.config["SESSION_COOKIE_HTTPONLY"] = True # impede que scripts no navegador (XSS) leiam o cookie de sessão
app.config["SESSION_COOKIE_SAMESITE"] = "Lax" # proteção extra contra CSRF em cookies

# DoS: ataque para derrubar o sistema com muitas requisições ou arquivos muito grandes
# XSS: injeção de javascript malicioso que pode roubar cookies ou rodar ações no navegador
# CSRF: site malicioso que força o navegador a enviar seus cookies para fazer requisição no seu nome

# inicializa o gerenciador de JWT
jwt = JWTManager(app)

# vincula o BD SQLAlchemy ao app
db.init_app(app)



# (2) INICIALIZAÇÃO DOS MODELS

with app.app_context():
    # importar classes do BD
    from app.models.like import Like
    from app.models.post import Post
    from app.models.user import User

    # cria as tabelas no SQLite caso ainda não existam
    db.create_all()


# (3) BLINDAGEM DO SISTEMA

@app.context_processor
def inserir_csrf_token():
    # injeta automaticamente a função de token CSRF em todos os templates HTML
    # isso impede que sites maliciosos forjem requisições em nome do usuário logado
    return {"csrf_token": gerar_csrf_token}


@app.after_request
def adicionar_cabecalhos_seguranca(response):
    # adiciona cabeçalhos HTTP em TODAS as respostas do servidor para proteção extra contra XSS e outros ataques
    response.headers["X-Content-Type-Options"] = "nosniff" # impede que o navegador "adivinhe" tipos de arquivos
    response.headers["X-Frame-Options"] = "DENY" # impede que o site seja aberto dentro de um iframe (evita Clickjacking)
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # ClickJacking: site falso coloca roda o site verdadeiro mas com botões falsos por cima
    
    # CSP: Content-Security-Policy (defesa contra XSS)
    # só permite carregar scripts e estilos do próprio site ou do Tailwind CSS
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "media-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    )
    return response


# REGISTRO DE ROTAS / CONTROLLERS

# lógica de negócio separada por módulos
from app.controllers import home_controller
from app.controllers import auth_controller
from app.controllers import post_controller

# mapeamento das URLs do site para as funções correspondentes nos controllers
app.add_url_rule(
    "/",
    "home",
    home_controller.home
)

# rotas do fluxo de registro e login
app.add_url_rule(
    "/login",
    "login",
    auth_controller.login,
    methods=["GET", "POST"]
)

app.add_url_rule(
    "/cadastro",
    "cadastro",
    auth_controller.cadastro,
    methods=["GET", "POST"]
)

# rota de área protegida
app.add_url_rule(
    "/perfil",
    "perfil",
    auth_controller.perfil
)

# rota de alteração de senha
app.add_url_rule(
    "/alterar-senha",
    "alterar_senha",
    auth_controller.alterar_senha,
    methods=["GET", "POST"]
)

# rota de logout do sistema
app.add_url_rule(
    "/logout",
    "logout",
    auth_controller.logout,
    methods=["POST"]
)

# rota para publicar
app.add_url_rule(
    "/publicar",
    "publicar",
    post_controller.publicar,
    methods=["GET", "POST"]
)

# rota para curtir
app.add_url_rule(
    "/post/<int:post_id>/like",
    "like_post",
    post_controller.like_post,
    methods=["POST"]
)



if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")