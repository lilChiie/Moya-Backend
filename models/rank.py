from api.extensions import db
from datetime import datetime
from flask import request

class Rank(db.Model):
    __tablename__ = 'ranks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    min_point = db.Column(db.Integer, nullable=True)
    max_point = db.Column(db.Integer, nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        avatar_url = self.avatar
        if avatar_url and avatar_url.startswith('/static/'):
            avatar_url = f"{request.host_url.rstrip('/')}{avatar_url}"
            
        return {
            "id": self.id,
            "name": self.name,
            "min_point": self.min_point,
            "max_point": self.max_point,
            "avatar": avatar_url,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
