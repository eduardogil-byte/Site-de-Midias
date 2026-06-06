from flask import flash, redirect, render_template, request, session, url_for
# Werkzeug: criptografia hash de senhas
from werkzeug.security import check_password_hash, generate_password_hash

# importações do banco de dados e dos Models
from app.database import db
from app.models.post import Post
from app.models.user import User
# decorador personalizado para checar o token CSRF nas requisições POST
from app.security import csrf_protect


# limpeza e validação básica de dados de entrada
def limpar_texto(valor, limite):

    valor = (valor or "").strip() # remove espaços em branco inúteis no início e fim
    return valor[:limite] # limita o tamanho máximo do texto


# controller do Fluxo de Cadastro de novos usuários
@csrf_protect # protege a rota contra ataques CSRF
def cadastro():
    if request.method == "GET": # se acessou a página
        return render_template("register.html")

    # se enviou o formulário (POST)
    nome = limpar_texto(request.form.get("nome"), 80)
    email = limpar_texto(request.form.get("email"), 120).lower()
    senha = request.form.get("senha") or ""

    # validação 1: busca se tem campos vazios
    if not nome or not email or not senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("cadastro"))

    # validação 2: exigência de tamanho mínimo de senha
    if len(senha) < 6:
        flash("A senha deve ter pelo menos 6 caracteres.", "erro")
        return redirect(url_for("cadastro"))

    # validação 3: consulta o Model para ver se o e-mail já existe no banco de dados
    usuario_existente = User.query.filter_by(email=email).first()

    if usuario_existente:
        flash("Este e-mail ja esta cadastrado.", "erro")
        return redirect(url_for("cadastro"))

    # se passar das validações cria a instância do novo usuário
    # o 'generate_password_hash' transforma a senha em um hash seguro
    novo_usuario = User(
        nome=nome,
        email=email,
        senha_hash=generate_password_hash(senha),
    )

    # adiciona o usuário no BD SQLite
    db.session.add(novo_usuario)
    db.session.commit()

    flash("Cadastro realizado com sucesso. Faca login para continuar.", "sucesso")
    return redirect(url_for("login"))


# controller do Fluxo de Login no sistema
@csrf_protect
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    # se for POST
    email = limpar_texto(request.form.get("email"), 120).lower()
    senha = request.form.get("senha") or ""

    if not email or not senha:
        flash("Preencha e-mail e senha.", "erro")
        return redirect(url_for("login"))

    # busca o usuário no banco
    usuario_encontrado = User.query.filter_by(email=email).first()

    # 'check_password_hash' compara de forma segura a senha digitada com o hash salvo no banco
    if usuario_encontrado is None or not check_password_hash(
        usuario_encontrado.senha_hash,
        senha,
    ):
        flash("E-mail ou senha invalidos.", "erro")
        return redirect(url_for("login"))

    # se o login deu certo, salva o ID do usuário na sessão do Flask
    # mantém conectado durante a navegação
    session["usuario_id"] = usuario_encontrado.id

    return redirect(url_for("home"))


# CONTROLLER de Exibição do Perfil do Usuário
def perfil():
    # recupera o ID do usuário que está guardado na sessão atual
    usuario_id = session.get("usuario_id")

    if not usuario_id:
        flash("Faca login para acessar seu perfil.", "erro")
        return redirect(url_for("login"))

    # busca os dados do usuário logado
    usuario = db.session.get(User, usuario_id)

    # se o usuário não for encontrado
    if usuario is None:
        session.pop("usuario_id", None) # destrói a sessão inválida
        flash("Sessao expirada. Faca login novamente.", "erro")
        return redirect(url_for("login"))

    # busca todos os posts criados especificamente por este usuário
    posts = Post.query.filter_by(usuario_id=usuario.id).order_by(Post.criado_em.desc()).all()

    # renderiza a página de perfil passando os dados do usuário e os seus posts para o HTML
    return render_template(
        "perfil.html",
        usuario=usuario.to_dict(),
        posts=posts,
    )


# CONTROLLER do Fluxo de Alteração de Senha por segurança
@csrf_protect
def alterar_senha():
    # bloqueia usuários não logados
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

    # se for POST, processa as senhas
    senha_atual = request.form.get("senha_atual") or ""
    nova_senha = request.form.get("nova_senha") or ""
    confirmar_senha = request.form.get("confirmar_senha") or ""

    if not senha_atual or not nova_senha or not confirmar_senha:
        flash("Preencha todos os campos.", "erro")
        return redirect(url_for("alterar_senha"))

    # validação 1: verifica se a senha atual digitada bate com o hash do banco
    if not check_password_hash(usuario.senha_hash, senha_atual):
        flash("Senha atual incorreta.", "erro")
        return redirect(url_for("alterar_senha"))

    # validação 2: garante que a nova senha tem ao menos 6 caracteres
    if len(nova_senha) < 6:
        flash("A nova senha deve ter pelo menos 6 caracteres.", "erro")
        return redirect(url_for("alterar_senha"))

    # validação 3: garante que o usuário digitou a nova senha igualmente nos dois campos
    if nova_senha != confirmar_senha:
        flash("A confirmacao da senha nao confere.", "erro")
        return redirect(url_for("alterar_senha"))

    # se tudo der certo, cria o hash
    usuario.senha_hash = generate_password_hash(nova_senha)
    db.session.commit() # salva alterações

    flash("Senha alterada com sucesso.", "sucesso")
    return redirect(url_for("perfil"))


# CONTROLLER de Encerramento de sessão
@csrf_protect # protegido por CSRF para evitar que sites externos forcem o logout do usuário
def logout():
    # remove a chave 'usuario_id' da sessão
    session.pop("usuario_id", None)
    flash("Logout realizado com sucesso.", "sucesso")
    return redirect(url_for("home")) # volta pra página inicial