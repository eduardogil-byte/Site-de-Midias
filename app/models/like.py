from datetime import datetime

from app.database import db


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    session_id = db.Column(db.String(128), nullable=False)
    criado_em = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    post = db.relationship("Post", back_populates="likes")

    __table_args__ = (
        db.UniqueConstraint("post_id", "session_id", name="uq_like_post_session"),
    )
