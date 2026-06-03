from flask import render_template, session

from app.database import db
from app.models.post import Post
from app.models.user import User


def home():
    posts = Post.query.order_by(Post.criado_em.desc()).all()
    usuario = None
    usuario_id = session.get("usuario_id")

    if usuario_id:
        usuario = db.session.get(User, usuario_id)

    return render_template("index.html", posts=posts, usuario=usuario)
