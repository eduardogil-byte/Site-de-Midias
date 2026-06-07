from datetime import datetime

# importação do banco de dados para mapear a tabela
from app.database import db


# MODEL que define a estrutura da tabela de curtidas no banco de dados
class Like(db.Model):
    __tablename__ = "likes"

    # 1. definição das colunas e chaves da tabela
    id = db.Column(db.Integer, primary_key=True) # chave primária
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False) # vincula a curtida ao ID do post
    session_id = db.Column(db.String(128), nullable=False) # guarda quem curtiu
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 2. relacionamento do SQLAlchemy para conseguir acessar os dados do post direto pelo objeto do Like
    post = db.relationship("Post", back_populates="likes")

    # 3. restrição de unicidade (UniqueConstraint)
    # garante que a combinação de um mesmo post com uma mesma sessão nunca se repita
    # isso impede que a mesma pessoa consiga dar 2 likes no mesmo post no banco de dados
    __table_args__ = (
        db.UniqueConstraint("post_id", "session_id", name="uq_like_post_session"),
    )