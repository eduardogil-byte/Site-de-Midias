import os
import secrets

from flask import flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from app.database import db
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.security import csrf_protect

EXTENSOES_IMAGEM = {"png", "jpg", "jpeg", "gif"}
EXTENSOES_VIDEO = {"mp4", "webm", "ogg"}
ASSINATURAS_PERMITIDAS = {
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "gif": [b"GIF87a", b"GIF89a"],
    "mp4": [b"\x00\x00\x00", b"ftyp"],
    "webm": [b"\x1a\x45\xdf\xa3"],
    "ogg": [b"OggS"],
}


def limpar_texto(valor, limite):
    valor = (valor or "").strip()
    return valor[:limite]


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


def assinatura_valida(arquivo, extensao):
    inicio = arquivo.stream.read(16)
    arquivo.stream.seek(0)

    assinaturas = ASSINATURAS_PERMITIDAS.get(extensao, [])

    if extensao == "mp4":
        return all(assinatura in inicio for assinatura in assinaturas)

    return any(inicio.startswith(assinatura) for assinatura in assinaturas)


def obter_identificador_like():
    usuario_id = session.get("usuario_id")

    if usuario_id:
        return f"user:{usuario_id}"

    session_id = session.get("like_session_id")

    if not session_id:
        session_id = secrets.token_urlsafe(32)
        session["like_session_id"] = session_id

    return f"anon:{session_id}"


def quer_resposta_json():
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or request.accept_mimetypes.best == "application/json"
    )


@csrf_protect
def publicar():
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Faca login para publicar.", "erro")
        return redirect(url_for("login"))

    usuario = db.session.get(User, usuario_id)

    if usuario is None:
        session.pop("usuario_id", None)
        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("create_post.html")

    titulo = limpar_texto(request.form.get("titulo"), 120)
    descricao = limpar_texto(request.form.get("descricao"), 1000)
    arquivo = request.files.get("arquivo")

    if not titulo or not descricao or not arquivo:
        flash("Preencha todos os campos e selecione um arquivo.", "erro")
        return redirect(url_for("publicar"))

    if arquivo.filename == "":
        flash("Nenhum arquivo foi selecionado.", "erro")
        return redirect(url_for("publicar"))

    extensao = pegar_extensao(arquivo.filename)
    tipo = verificar_tipo_arquivo(arquivo.filename)

    if tipo is None:
        flash("Formato de arquivo nao permitido.", "erro")
        return redirect(url_for("publicar"))

    if not assinatura_valida(arquivo, extensao):
        flash("O conteudo do arquivo nao confere com o formato informado.", "erro")
        return redirect(url_for("publicar"))

    nome_seguro = secure_filename(arquivo.filename)
    nome_final = f"{secrets.token_hex(16)}_{nome_seguro}"

    if tipo == "imagem":
        pasta_upload = os.path.abspath("app/static/uploads/images")
    else:
        pasta_upload = os.path.abspath("app/static/uploads/videos")

    os.makedirs(pasta_upload, exist_ok=True)

    caminho_arquivo = os.path.join(pasta_upload, nome_final)
    arquivo.save(caminho_arquivo)

    novo_post = Post(
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
        titulo=titulo,
        descricao=descricao,
        tipo=tipo,
        arquivo=nome_final,
    )

    db.session.add(novo_post)
    db.session.commit()

    return redirect(url_for("home"))


@csrf_protect
def like_post(post_id):
    post = db.session.get(Post, post_id)

    if post is None:
        if quer_resposta_json():
            return jsonify({"ok": False, "message": "Publicacao nao encontrada."}), 404

        flash("Publicacao nao encontrada.", "erro")
        return redirect(url_for("home"))

    session_id = obter_identificador_like()

    like_existente = Like.query.filter_by(
        post_id=post.id,
        session_id=session_id,
    ).first()

    if like_existente:
        if quer_resposta_json():
            return jsonify(
                {
                    "ok": False,
                    "message": "Voce ja curtiu esta publicacao.",
                    "likes": post.total_likes,
                }
            ), 409

        flash("Voce ja curtiu esta publicacao.", "erro")
        return redirect(url_for("home"))

    db.session.add(Like(post_id=post.id, session_id=session_id))
    db.session.commit()

    if quer_resposta_json():
        return jsonify({"ok": True, "likes": post.total_likes})

    return redirect(url_for("home"))
