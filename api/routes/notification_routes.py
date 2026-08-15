from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from models.notification import Notification

notification_bp = Blueprint('notification', __name__)

@notification_bp.route('/', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = int(get_jwt_identity())
    
    # Ambil notifikasi milik user yang sedang login, urutkan dari yang terbaru
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    return jsonify({
        "success": True,
        "data": [notif.to_dict() for notif in notifications]
    }), 200

@notification_bp.route('/read/<int:id>', methods=['PUT'])
@jwt_required()
def mark_as_read(id):
    user_id = int(get_jwt_identity())
    
    # Pastikan notifikasi ini milik user yang sedang login
    notification = Notification.query.filter_by(id=id, user_id=user_id).first()
    
    if not notification:
        return jsonify({"success": False, "message": "Notification not found"}), 404
        
    notification.is_read = True
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }), 500
