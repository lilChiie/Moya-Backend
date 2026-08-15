from api.extensions import db
from datetime import datetime
from flask import request

destination_tourisms = db.Table('destination_tourisms',
    db.Column('destination_id', db.Integer, db.ForeignKey('destinations.id'), primary_key=True),
    db.Column('tourism_id', db.Integer, db.ForeignKey('tourism.id'), primary_key=True)
)

destination_accessibilities = db.Table('destination_accessibilities',
    db.Column('destination_id', db.Integer, db.ForeignKey('destinations.id'), primary_key=True),
    db.Column('accessibility_id', db.Integer, db.ForeignKey('accessibility.id'), primary_key=True)
)

class Destination(db.Model):
    __tablename__ = 'destinations'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Numeric(10, 7), nullable=True)
    longitude = db.Column(db.Numeric(10, 7), nullable=True)
    radius = db.Column(db.Numeric(8, 2), nullable=True)
    entrance_fee = db.Column(db.Numeric(12, 2), default=0.00, nullable=True)
    estimated_duration = db.Column(db.Integer, nullable=True)
    cleanliness_score = db.Column(db.Numeric(5, 4), default=0.5000, nullable=True)
    cleanliness_status = db.Column(db.String(30), nullable=False, default='Safe')
    opening_time = db.Column(db.Time, nullable=True)
    closing_time = db.Column(db.Time, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tourisms = db.relationship('Tourism', secondary=destination_tourisms, lazy='subquery', backref=db.backref('destinations', lazy=True))
    accessibilities = db.relationship('Accessibility', secondary=destination_accessibilities, lazy='subquery', backref=db.backref('destinations', lazy=True))

    def to_dict(self):
        img_url = self.image_url
        if img_url and img_url.startswith('/static/'):
            img_url = f"{request.host_url.rstrip('/')}{img_url}"
            
        return {
            "id": self.id,
            "tourism_id": [t.id for t in self.tourisms],
            "accessibility_id": [a.id for a in self.accessibilities],
            "name": self.name,
            "description": self.description,
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "radius": float(self.radius) if self.radius is not None else None,
            "entrance_fee": float(self.entrance_fee) if self.entrance_fee is not None else None,
            "estimated_duration": self.estimated_duration,
            "cleanliness_score": float(self.cleanliness_score) if self.cleanliness_score is not None else 0.5,
            "cleanliness_status": self.cleanliness_status,
            "opening_time": self.opening_time.strftime('%H:%M:%S') if self.opening_time else None,
            "closing_time": self.closing_time.strftime('%H:%M:%S') if self.closing_time else None,
            "image_url": img_url,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }
