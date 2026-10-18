from api.extensions import db
from datetime import datetime
from flask import request


class CleanReport(db.Model):
    __tablename__ = 'clean_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    destination_id = db.Column(
        db.Integer, db.ForeignKey('destinations.id'), nullable=False
    )
    image_url = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum('pending', 'verified', 'rejected', name='clean_report_status'),
        nullable=False,
        default='pending'
    )
    admin_notes = db.Column(db.Text, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship('User', backref=db.backref('clean_reports', lazy=True))
    destination = db.relationship(
        'Destination', backref=db.backref('clean_reports', lazy=True)
    )

    def to_dict(self):
        img_url = self.image_url
        if img_url and img_url.startswith('/static/'):
            img_url = f"{request.host_url.rstrip('/')}{img_url}"

        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "destination_id": self.destination_id,
            "destination_name": self.destination.name if self.destination else None,
            "image_url": img_url,
            "notes": self.notes,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "verified_at": self.verified_at.strftime("%Y-%m-%d %H:%M:%S") if self.verified_at else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
