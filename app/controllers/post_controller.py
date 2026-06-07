import os
import secrets

from flask import flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

# importação do BD, dos Models e segurança necessários
from app.database import db
from app.models.like import Like
from app.models.post import Post
from app.models.user import User
from app.security import csrf_protect

# configurações de upload de arquivos permitidos
EXTENSOES_IMAGEM = {"png", "jpg", "jpeg", "gif"}
EXTENSOES_VIDEO = {"mp4", "webm", "ogg"}

# assinaturas em bytes (magic numbers) para cada tipo de arquivo
# isso previne que arquivos maliciosos renomeados sejam aceitos
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
    # limpa o texto removendo espaços extras e corta no limite do banco de dados
    valor = (valor or "").strip()
    return valor[:limite]


def pegar_extensao(nome_arquivo):
    # extrai a extensão do arquivo (.png, .gif...)
    if "." not in nome_arquivo:
        return ""

    return nome_arquivo.rsplit(".", 1)[1].lower()


def verificar_tipo_arquivo(nome_arquivo):
    # verifica se a extensão do arquivo está na lista de imagens ou vídeos permitidos
    extensao = pegar_extensao(nome_arquivo)

    if extensao in EXTENSOES_IMAGEM:
        return "imagem"

    if extensao in EXTENSOES_VIDEO:
        return "video"

    return None


def assinatura_valida(arquivo, extensao):
    # lê os primeiros 16 bytes do arquivo e compara com a assinatura real para evitar fraudes
    inicio = arquivo.stream.read(16)
    arquivo.stream.seek(0) # retorna o cursor pro início pra não estragar o salvamento depois

    assinaturas = ASSINATURAS_PERMITIDAS.get(extensao, [])

    if extensao == "mp4":
        return all(assinatura in inicio for assinatura in assinaturas)

    return any(inicio.startswith(assinatura) for assinatura in assinaturas)


def obter_identificador_like():
    # identificador único para quem está curtindo
    usuario_id = session.get("usuario_id")

    if usuario_id:
        return f"user:{usuario_id}" # usa o id do usuário se estiver logado

    session_id = session.get("like_session_id")

    if not session_id:
        session_id = secrets.token_urlsafe(32)
        session["like_session_id"] = session_id

    return f"anon:{session_id}"


def quer_resposta_json():
    # verifica se a requisição veio do javascript (fetch) para não recarregar a tela inteira
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or request.accept_mimetypes.best == "application/json"
    )


def total_likes_post(post_id):
    # conta o total de curtidas de um post específico no banco
    return Like.query.filter_by(post_id=post_id).count()


# CONTROLLER da Lógica de criar nova publicação
@csrf_protect
def publicar():
    # 1. verifica se existe um usuário logado na sessão atual
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Faca login para publicar.", "erro")
        return redirect(url_for("login"))

    usuario = db.session.get(User, usuario_id)

    if usuario is None:
        session.pop("usuario_id", None)
        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    # 2. se for um acesso normal (GET), renderiza a tela do formulário
    if request.method == "GET":
        return render_template("create_post.html")

    # 3. recebe os dados do formulário e limpa os textos
    titulo = limpar_texto(request.form.get("titulo"), 120)
    descricao = limpar_texto(request.form.get("descricao"), 1000)
    arquivo = request.files.get("arquivo")

    if not titulo or not arquivo:
        flash("Preencha o titulo e selecione um arquivo.", "erro")
        return redirect(url_for("publicar"))

    if arquivo.filename == "":
        flash("Nenhum arquivo foi selecionado.", "erro")
        return redirect(url_for("publicar"))

    # 4. checagem de segurança do arquivo enviado
    extensao = pegar_extensao(arquivo.filename)
    tipo = verificar_tipo_arquivo(arquivo.filename)

    if tipo is None:
        flash("Formato de arquivo nao permitido.", "erro")
        return redirect(url_for("publicar"))

    if not assinatura_valida(arquivo, extensao):
        flash("O conteudo do arquivo nao confere com o formato informado.", "erro")
        return redirect(url_for("publicar"))

    # 5. prepara o nome seguro para salvar no servidor
    # secure_filename remove caracteres que hackers usam pra invadir pastas
    nome_seguro = secure_filename(arquivo.filename)
    nome_final = f"{secrets.token_hex(16)}_{nome_seguro}" # adiciona um código aleatório para não sobrescrever arquivos

    # 6. define a pasta correta baseada no tipo de arquivo e cria ela se não existir
    if tipo == "imagem":
        pasta_upload = os.path.abspath("app/static/uploads/images")
    else:
        pasta_upload = os.path.abspath("app/static/uploads/videos")

    os.makedirs(pasta_upload, exist_ok=True)

    # salva fisicamente o arquivo no computador/servidor
    caminho_arquivo = os.path.join(pasta_upload, nome_final)
    arquivo.save(caminho_arquivo)

    # 7. cria a publicação no banco de dados e vincula ao usuário logado
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

    flash("Publicacao criada com sucesso.", "sucesso")
    return redirect(url_for("home"))


# CONTROLLER da Lógica de curtir ou descurtir uma publicação
@csrf_protect
def like_post(post_id):
    # 1. busca se a publicação existe no banco de dados
    post = db.session.get(Post, post_id)

    if post is None:
        if quer_resposta_json():
            return jsonify({"ok": False, "message": "Publicacao nao encontrada."}), 404

        flash("Publicacao nao encontrada.", "erro")
        return redirect(url_for("home"))

    # 2. verifica se o usuário está logado
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        if quer_resposta_json():
            return jsonify(
                {
                    "ok": False,
                    "message": "Faca login para curtir publicacoes.",
                    "redirect": url_for("login"),
                    "likes": post.total_likes,
                }
            ), 401

        flash("Faca login para curtir publicacoes.", "erro")
        return redirect(url_for("login"))

    usuario = db.session.get(User, usuario_id)

    if usuario is None:
        session.pop("usuario_id", None)

        if quer_resposta_json():
            return jsonify(
                {
                    "ok": False,
                    "message": "Sessao expirada. Faca login novamente.",
                    "redirect": url_for("login"),
                    "likes": post.total_likes,
                }
            ), 401

        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    # 3. identifica quem é o usuário dando o like e busca se ele já curtiu
    session_id = obter_identificador_like()

    like_existente = Like.query.filter_by(
        post_id=post.id,
        session_id=session_id,
    ).first()

    # 4. sistema liga/desliga: se já existe a curtida, ele apaga do banco
    if like_existente:
        db.session.delete(like_existente)
        db.session.commit()

        if quer_resposta_json():
            return jsonify(
                {
                    "ok": True,
                    "liked": False, # avisa pro javascript desligar a cor do botão
                    "likes": total_likes_post(post.id),
                }
            )

        flash("Curtida removida.", "sucesso")
        return redirect(url_for("home"))

    # 5. se não existia, salva a nova curtida no banco
    db.session.add(Like(post_id=post.id, session_id=session_id))

    try:
        db.session.commit()
    except IntegrityError:
        # proteção extra: se o usuário clicar 2x muito rápido o banco impede erro de duplicação
        db.session.rollback()
        like_existente = Like.query.filter_by(
            post_id=post.id,
            session_id=session_id,
        ).first()

        if like_existente:
            db.session.delete(like_existente)
            db.session.commit()

        if quer_resposta_json():
            return jsonify(
                {
                    "ok": True,
                    "liked": False,
                    "likes": total_likes_post(post.id),
                }
            )

        flash("Curtida removida.", "sucesso")
        return redirect(url_for("home"))

    # 6. envia as informações de sucesso de volta para o usuário
    if quer_resposta_json():
        return jsonify(
            {
                "ok": True,
                "liked": True, # avisa pro javascript ligar a cor do botão
                "likes": total_likes_post(post.id),
            }
        )

    flash("Publicacao curtida.", "sucesso")
    return redirect(url_for("home"))