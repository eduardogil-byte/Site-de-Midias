from flask import Flask
from flask_jwt_extended import JWTManager
import os

template_dir = os.path.abspath("app/views/templates")

static_dir = os.path.abspath("app/static")

app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=static_dir
)

app.config["SECRET_KEY"] = "chave-secreta-do-projeto"

app.config["JWT_SECRET_KEY"] = "chave-secreta-jwt-do-projeto"

jwt = JWTManager(app)

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
    app.run(debug=True)