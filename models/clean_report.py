from api.extensions import db
from flask import request, has_request_context
from api.utils import now_wib


class CleanReport(db.Model):
    __tablename__ = 'clean_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    report_id = db.Column(
        db.Integer, db.ForeignKey('reports.id'), nullable=False
    )
    image_url = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=now_wib)
    updated_at = db.Column(
        db.DateTime,
        default=now_wib,
        onupdate=now_wib
    )

    user = db.relationship('User', backref=db.backref('clean_reports', lazy=True))
    report = db.relationship('Report', backref=db.backref('clean_reports', lazy=True))

    def to_dict(self):
        img_url = self.image_url
        if img_url and img_url.startswith('/static/') and has_request_context():
            img_url = f"{request.host_url.rstrip('/')}{img_url}"

        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "report_id": self.report_id,
            "destination_id": self.report.destination_id if self.report else None,
            "destination_name": (
                self.report.destination.name
                if self.report and self.report.destination else None
            ),
            "image_url": img_url,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }
