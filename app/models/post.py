from datetime import datetime

# importação do banco de dados para mapear a tabela
from app.database import db


# MODEL que define a estrutura da tabela de publicações (Posts) no banco de dados
class Post(db.Model):
    __tablename__ = "posts"

    # 1. definição das colunas e chaves da tabela
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True) # vincula o post ao ID do autor
    usuario_nome = db.Column(db.String(80), nullable=False) # nome do autor
    titulo = db.Column(db.String(120), nullable=False) # título da publicação
    descricao = db.Column(db.Text, nullable=False) # texto descritivo do post
    tipo = db.Column(db.String(20), nullable=False) # "imagem" ou "video"
    arquivo = db.Column(db.String(255), nullable=False) # guarda o nome do arquivo gerado pelo secrets no servidor
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 2. relacionamentos do SQLAlchemy para conectar as tabelas
    usuario = db.relationship("User", back_populates="posts") # permite acessar os dados do autor direto pelo post
    
    # relação com a tabela Like: se o post for deletado, apaga todas as curtidas dele automaticamente (cascade)
    likes = db.relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True,
    )

    # 3. propriedade dinâmica para contar as curtidas
    # funciona como um campo comum do banco, mas calcula o total de likes em tempo real
    @property
    def total_likes(self):
        return len(self.likes)