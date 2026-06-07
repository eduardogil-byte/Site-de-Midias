from flask import render_template, session

# importação do BD e dos Models necessários
from app.database import db
from app.models.like import Like
from app.models.post import Post
from app.models.user import User


# CONTROLLER da Lógica da página inicial (Home)
def home():
    # 1. busca todos os posts salvos no banco de dados, ordenando dos mais recentes para os mais antigos
    # o SQLAlchemy faz essa consulta de forma segura, prevenindo ataques de SQL Injection
    posts = Post.query.order_by(Post.criado_em.desc()).all()
    
    # inicializa variáveis padrão para visitantes
    usuario = None
    posts_curtidos = set() # um set (conjunto) para buscas rápidas no HTML
    
    # 2. verifica se existe um usuário logado na sessão atual
    usuario_id = session.get("usuario_id")

    # se o usuário estiver logado, carrega as informações personalizadas dele
    if usuario_id:
        # busca os dados
        usuario = db.session.get(User, usuario_id)

        if usuario:
            identificador_like = f"user:{usuario.id}"
            
            # 3. busca no banco todas as curtidas que esse usuário deu
            # extrai apenas os IDs dos posts curtidos
            posts_curtidos = {
                like.post_id
                for like in Like.query.filter_by(session_id=identificador_like).all()
            }

    # 4. renderização da view: envia todos os dados coletados para o arquivo 'index.html'
    # Jinja2 renderiza as coisas da tela do usuário
    return render_template(
        "index.html",
        posts=posts,                   # todos os posts que serão exibidos no feed
        usuario=usuario,               # dados do usuário logado (se for None, mostra o botão de Login)
        posts_curtidos=posts_curtidos, # conjunto de IDs para o HTML saber quais botões de curtir devem estar ativos
    )