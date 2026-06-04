from flask import render_template, session

from app.database import db
from app.models.like import Like
from app.models.post import Post
from app.models.user import User


def home():
    posts = Post.query.order_by(Post.criado_em.desc()).all()
    usuario = None
    posts_curtidos = set()
    usuario_id = session.get("usuario_id")

    if usuario_id:
        usuario = db.session.get(User, usuario_id)

        if usuario:
            identificador_like = f"user:{usuario.id}"
            posts_curtidos = {
                like.post_id
                for like in Like.query.filter_by(session_id=identificador_like).all()
            }

    return render_template(
        "index.html",
        posts=posts,
        usuario=usuario,
        posts_curtidos=posts_curtidos,
    )
