from api.extensions import db
from models.user import User
from models.destination import Destination
from models.accessibility import Accessibility
from models.tourism import Tourism
from models.rank import Rank

class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(
        db.Integer, db.ForeignKey("destinations.id"), nullable=False
    )
    image_url = db.Column(db.String(255), nullable=False)
    user_notes = db.Column(db.Text)
    admin_notes = db.Column(db.Text)
    status = db.Column(
        db.Enum("pending", "process", "resolved"),
        nullable=False,
        default="pending"
    )
    detected_count = db.Column(db.Integer, nullable=False, default=0)
    score = db.Column(db.Numeric(4, 2), nullable=False, default=0.00)
    created_at = db.Column(
        db.DateTime, nullable=False, server_default=db.func.current_timestamp()
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    user = db.relationship("User", backref="reports")
    destination = db.relationship("Destination", backref="reports")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(
        db.Integer, db.ForeignKey("destinations.id"), nullable=False
    )
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User", backref="reviews")
    destination = db.relationship("Destination", backref="reviews")
    points = db.relationship(
        "UserPoint", back_populates="review", cascade="all, delete-orphan"
    )


class UserPoint(db.Model):
    __tablename__ = "user_points"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    points = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    user = db.relationship("User", backref="points")
    review = db.relationship("Review", back_populates="points")


class UserVisit(db.Model):
    __tablename__ = "user_visits"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    destination_id = db.Column(
        db.Integer, db.ForeignKey("destinations.id"), nullable=False
    )
    visited_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User", backref="visits")
    destination = db.relationship("Destination", backref="visits")


class RecomRequest(db.Model):
    __tablename__ = "recom_requests"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    accessibility_id = db.Column(
        db.Integer, db.ForeignKey("accessibility.id"), nullable=False
    )
    tourism_id = db.Column(db.Integer, db.ForeignKey("tourism.id"), nullable=False)
    budget = db.Column(db.Numeric(12, 2), default=0.00)
    duration_minutes = db.Column(db.Integer)
    max_distance_km = db.Column(db.Numeric(8, 2))
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    user = db.relationship("User", backref="recom_requests")
    accessibility = db.relationship("Accessibility", backref="recom_requests")
    tourism = db.relationship("Tourism", backref="recom_requests")
    results = db.relationship(
        "RecomResult", back_populates="request", cascade="all, delete-orphan"
    )
    itineraries = db.relationship(
        "Itinerary", back_populates="recom_request", cascade="all, delete-orphan"
    )


class RecomResult(db.Model):
    __tablename__ = "recom_results"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(
        db.Integer, db.ForeignKey("recom_requests.id"), nullable=False
    )
    destination_id = db.Column(
        db.Integer, db.ForeignKey("destinations.id"), nullable=False
    )
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    request = db.relationship("RecomRequest", back_populates="results")
    destination = db.relationship("Destination", backref="recom_results")


class Itinerary(db.Model):
    __tablename__ = "itineraries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recom_request_id = db.Column(
        db.Integer, db.ForeignKey("recom_requests.id"), nullable=False
    )
    name = db.Column(db.String(150), nullable=False)
    route_type = db.Column(
        db.Enum("DSS", "manual"), nullable=False, default="DSS"
    )
    total_duration = db.Column(db.Integer)
    total_cost = db.Column(db.Numeric(12, 2), default=0.00)
    detected_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("User", backref="itineraries")
    recom_request = db.relationship("RecomRequest", back_populates="itineraries")
    items = db.relationship(
        "ItineraryItem", back_populates="itinerary", cascade="all, delete-orphan"
    )


class ItineraryItem(db.Model):
    __tablename__ = "itinerary_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    itinerary_id = db.Column(
        db.Integer, db.ForeignKey("itineraries.id"), nullable=False
    )
    destination_id = db.Column(
        db.Integer, db.ForeignKey("destinations.id"), nullable=False
    )
    sequence = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )

    itinerary = db.relationship("Itinerary", back_populates="items")
    destination = db.relationship("Destination", backref="itinerary_items")