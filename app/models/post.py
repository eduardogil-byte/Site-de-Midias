from datetime import datetime

from app.database import db


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    usuario_nome = db.Column(db.String(80), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    arquivo = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    usuario = db.relationship("User", back_populates="posts")
    likes = db.relationship(
        "Like",
        back_populates="post",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def total_likes(self):
        return len(self.likes)
