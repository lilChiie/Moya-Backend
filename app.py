from flask import Flask

from config import Config
from api.extensions import db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    # Mendaftarkan Blueprint untuk API Auth
    from api.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Blueprint Tourism
    from api.routes.tourism_routes import tourism_bp
    app.register_blueprint(tourism_bp, url_prefix='/api/tourism')

    # Blueprint Accessibility
    from api.routes.accessibility_routes import accessibility_bp
    app.register_blueprint(accessibility_bp, url_prefix='/api/accessibility')

    # Blueprint Destinations
    from api.routes.destination_routes import destination_bp
    app.register_blueprint(destination_bp, url_prefix='/api/destinations')

    # Blueprint Ranks
    from api.routes.rank_routes import rank_bp
    app.register_blueprint(rank_bp, url_prefix='/api/ranks')

    # Blueprint Recommendation
    from api.routes.recommendation import recommendation_bp
    app.register_blueprint(recommendation_bp, url_prefix='/api/recommendation')

    # Blueprint Reports
    from api.routes.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/api/reports')

    # Blueprint Profile
    from api.routes.profile_routes import profile_bp
    app.register_blueprint(profile_bp, url_prefix='/api/profile')

    # Blueprint Leaderboard
    from api.routes.leaderboard_routes import leaderboard_bp
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')

    # Blueprint Notification
    from api.routes.notification_routes import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')

    # Blueprint Spots
    from api.routes.spots import spot_bp
    app.register_blueprint(spot_bp, url_prefix='/api/spots')
    
    return app


app = create_app()


@app.route("/")
def home():
    return {
        "success": True,
        "message": "Moya API is running"
    }


if __name__ == "__main__":
    app.run(debug=True)