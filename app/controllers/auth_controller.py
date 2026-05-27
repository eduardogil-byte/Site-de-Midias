from flask import render_template, request, redirect, url_for, flash
from flask_jwt_extended import create_access_token


# Lista temporária para simular usuários cadastrados
# Depois vamos trocar isso pelo MySQL
usuarios = []


def cadastro():
    if request.method == "GET":
        return render_template("register.html")

    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")

    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("cadastro"))

    for usuario in usuarios:
        if usuario["email"] == email:
            flash("Este e-mail já está cadastrado.", "erro")
            return redirect(url_for("cadastro"))

    novo_usuario = {
        "id": len(usuarios) + 1,
        "nome": nome,
        "email": email,
        "senha": senha
    }

    usuarios.append(novo_usuario)

    flash("Cadastro realizado com sucesso! Faça login.", "sucesso")
    return redirect(url_for("login"))


def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email")
    senha = request.form.get("senha")

    if not email or not senha:
        flash("Preencha e-mail e senha.", "erro")
        return redirect(url_for("login"))

    usuario_encontrado = None

    for usuario in usuarios:
        if usuario["email"] == email and usuario["senha"] == senha:
            usuario_encontrado = usuario
            break

    if usuario_encontrado is None:
        flash("E-mail ou senha inválidos.", "erro")
        return redirect(url_for("login"))

    access_token = create_access_token(
        identity=str(usuario_encontrado["id"])
    )

    flash("Login realizado com sucesso!", "sucesso")

    return render_template(
        "perfil.html",
        usuario=usuario_encontrado,
        token=access_token
    )