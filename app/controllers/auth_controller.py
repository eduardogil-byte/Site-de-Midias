from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.models.post import Post
from app.models.user import User
from app.security import csrf_protect


def limpar_texto(valor, limite):
    valor = (valor or "").strip()
    return valor[:limite]


@csrf_protect
def cadastro():
    if request.method == "GET":
        return render_template("register.html")

    nome = limpar_texto(request.form.get("nome"), 80)
    email = limpar_texto(request.form.get("email"), 120).lower()
    senha = request.form.get("senha") or ""

    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("cadastro"))

    if len(senha) < 6:
        flash("A senha deve ter pelo menos 6 caracteres.", "erro")
        return redirect(url_for("cadastro"))

    usuario_existente = User.query.filter_by(email=email).first()

    if usuario_existente:
        flash("Este e-mail ja esta cadastrado.", "erro")
        return redirect(url_for("cadastro"))

    novo_usuario = User(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash(senha),
    )

    db.session.add(novo_usuario)
    db.session.commit()

    flash("Cadastro realizado com sucesso. Faca login para continuar.", "sucesso")
    return redirect(url_for("login"))


@csrf_protect
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = limpar_texto(request.form.get("email"), 120).lower()
    senha = request.form.get("senha") or ""

    if not email or not senha:
        flash("Preencha e-mail e senha.", "erro")
        return redirect(url_for("login"))

    usuario_encontrado = User.query.filter_by(email=email).first()

    if usuario_encontrado is None or not check_password_hash(
        usuario_encontrado.senha_hash,
        senha,
    ):
        flash("E-mail ou senha invalidos.", "erro")
        return redirect(url_for("login"))

    session["usuario_id"] = usuario_encontrado.id

    return redirect(url_for("home"))


def perfil():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Faca login para acessar seu perfil.", "erro")
        return redirect(url_for("login"))

    usuario = db.session.get(User, usuario_id)

    if usuario is None:
        session.pop("usuario_id", None)
        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    posts = Post.query.filter_by(usuario_id=usuario.id).order_by(Post.criado_em.desc()).all()

    return render_template(
        "perfil.html",
        usuario=usuario.to_dict(),
        posts=posts,
    )


@csrf_protect
def alterar_senha():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Faca login para alterar sua senha.", "erro")
        return redirect(url_for("login"))

    usuario = db.session.get(User, usuario_id)

    if usuario is None:
        session.pop("usuario_id", None)
        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("alterar_senha.html")

    senha_atual = request.form.get("senha_atual") or ""
    nova_senha = request.form.get("nova_senha") or ""
    confirmar_senha = request.form.get("confirmar_senha") or ""

    if not senha_atual or not nova_senha or not confirmar_senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("alterar_senha"))

    if not check_password_hash(usuario.senha_hash, senha_atual):
        flash("Senha atual incorreta.", "erro")
        return redirect(url_for("alterar_senha"))

    if len(nova_senha) < 6:
        flash("A nova senha deve ter pelo menos 6 caracteres.", "erro")
        return redirect(url_for("alterar_senha"))

    if nova_senha != confirmar_senha:
        flash("A confirmacao da senha nao confere.", "erro")
        return redirect(url_for("alterar_senha"))

    usuario.senha_hash = generate_password_hash(nova_senha)
    db.session.commit()

    flash("Senha alterada com sucesso.", "sucesso")
    return redirect(url_for("perfil"))


@csrf_protect
def logout():
    session.pop("usuario_id", None)
    flash("Logout realizado com sucesso.", "sucesso")
    return redirect(url_for("home"))
