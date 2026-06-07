from app.database import db


# MODEL que define a estrutura da tabela de usuários (Users) no banco de dados
class User(db.Model):
    __tablename__ = "users"

    # 1. definição das colunas e chaves da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True) # único e indexado para buscas rápidas no login
    senha_hash = db.Column(db.String(255), nullable=False) # guarda a senha criptografada

    # 2. relacionamento do SQLAlchemy para conectar as tabelas
    posts = db.relationship("Post", back_populates="usuario", lazy=True) # permite acessar a lista de posts do usuário

    # 3. método para converter os dados do objeto em um dicionário Python
    # útil caso o sistema precise enviar os dados do usuário em formato JSON no futuro
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
        }