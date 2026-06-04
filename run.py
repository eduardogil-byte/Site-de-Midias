from flask import Flask
from flask_jwt_extended import JWTManager
import os

from app.database import db
from app.security import gerar_csrf_token

template_dir = os.path.abspath("app/views/templates")

static_dir = os.path.abspath("app/static")

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "midiahub-chave-de-desenvolvimento-com-mais-de-32-bytes",
)

app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY",
    "midiahub-chave-jwt-de-desenvolvimento-com-mais-de-32-bytes",
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///midiahub.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

jwt = JWTManager(app)

db.init_app(app)

with app.app_context():
    from app.models.like import Like
    from app.models.post import Post
    from app.models.user import User

    db.create_all()


@app.context_processor
def inserir_csrf_token():
    return {"csrf_token": gerar_csrf_token}


@app.after_request
def adicionar_cabecalhos_seguranca(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
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

from app.controllers import home_controller
from app.controllers import auth_controller
from app.controllers import post_controller

app.add_url_rule(
    "/",
    "home",
    home_controller.home
)

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

app.add_url_rule(
    "/perfil",
    "perfil",
    auth_controller.perfil
)

app.add_url_rule(
    "/alterar-senha",
    "alterar_senha",
    auth_controller.alterar_senha,
    methods=["GET", "POST"]
)

app.add_url_rule(
    "/logout",
    "logout",
    auth_controller.logout,
    methods=["POST"]
)

app.add_url_rule(
    "/publicar",
    "publicar",
    post_controller.publicar,
    methods=["GET", "POST"]
)

app.add_url_rule(
    "/post/<int:post_id>/like",
    "like_post",
    post_controller.like_post,
    methods=["POST"]
)

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
