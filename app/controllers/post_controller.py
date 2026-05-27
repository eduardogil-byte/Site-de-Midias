from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import time

posts = []

EXTENSOES_IMAGEM = {"png", "jpg", "jpeg", "gif"}
EXTENSOES_VIDEO = {"mp4", "webm", "ogg"}


def pegar_extensao(nome_arquivo):
    if "." not in nome_arquivo:
        return ""

    return nome_arquivo.rsplit(".", 1)[1].lower()


def verificar_tipo_arquivo(nome_arquivo):
    extensao = pegar_extensao(nome_arquivo)

    if extensao in EXTENSOES_IMAGEM:
        return "imagem"

    if extensao in EXTENSOES_VIDEO:
        return "video"

    return None


def publicar():
    if request.method == "GET":
        return render_template("create_post.html")

    titulo = request.form.get("titulo")
    descricao = request.form.get("descricao")
    arquivo = request.files.get("arquivo")

    if not titulo or not descricao or not arquivo:
        flash("Preencha todos os campos e selecione um arquivo.", "erro")
        return redirect(url_for("publicar"))

    if arquivo.filename == "":
        flash("Nenhum arquivo foi selecionado.", "erro")
        return redirect(url_for("publicar"))

    tipo = verificar_tipo_arquivo(arquivo.filename)

    if tipo is None:
        flash("Formato de arquivo não permitido.", "erro")
        return redirect(url_for("publicar"))

    nome_seguro = secure_filename(arquivo.filename)

    nome_final = f"{int(time.time())}_{nome_seguro}"

    if tipo == "imagem":
        pasta_upload = os.path.abspath("app/static/uploads/images")
    else:
        pasta_upload = os.path.abspath("app/static/uploads/videos")

    os.makedirs(pasta_upload, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_upload, nome_final)

    arquivo.save(caminho_arquivo)

    novo_post = {
        "id": len(posts) + 1,
        "usuario": "Usuário logado",
        "titulo": titulo,
        "descricao": descricao,
        "tipo": tipo,
        "arquivo": nome_final,
        "likes": 0
    }

    posts.append(novo_post)

    flash("Publicação criada com sucesso!", "sucesso")
    return redirect(url_for("home"))


def like_post(post_id):
    for post in posts:
        if post["id"] == post_id:
            post["likes"] += 1
            flash("Você curtiu a publicação!", "sucesso")
            return redirect(url_for("home"))

    flash("Publicação não encontrada.", "erro")
    return redirect(url_for("home"))