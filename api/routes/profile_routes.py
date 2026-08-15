from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from api.extensions import db
from api.models import UserPoint
from models.user import User
from models.rank import Rank
from models.notification import Notification
from sqlalchemy import func

profile_bp = Blueprint('profile', __name__)


def get_user_rank(user_id):
    """Menghitung total point user dan mencocokkan dengan rank yang sesuai."""
    
    total_points = db.session.query(
        func.coalesce(func.sum(UserPoint.points), 0)
    ).filter(UserPoint.user_id == user_id).scalar()
    
    total_points = int(total_points)
    
    # Cari rank yang cocok berdasarkan min_point dan max_point
    rank = Rank.query.filter(
        Rank.min_point <= total_points,
        Rank.max_point >= total_points
    ).first()
    
    # Jika tidak ada rank yang cocok, ambil rank tertinggi yang masih di bawah total point
    if not rank:
        rank = Rank.query.filter(
            Rank.min_point <= total_points
        ).order_by(Rank.min_point.desc()).first()
    
    # Jika masih tidak ada, ambil rank terendah
    if not rank:
        rank = Rank.query.order_by(Rank.min_point.asc()).first()
    
    # Build avatar URL
    avatar_url = None
    if rank and rank.avatar:
        avatar_url = rank.avatar
        if avatar_url.startswith('/static/'):
            avatar_url = f"{request.host_url.rstrip('/')}{avatar_url}"
    
    return {
        "total_points": total_points,
        "rank_id": rank.id if rank else None,
        "rank_name": rank.name if rank else None,
        "avatar": avatar_url
    }


# Get profile (data user yang sedang login)
@profile_bp.route('/', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    rank_info = get_user_rank(user_id)
    
    return jsonify({
        "success": True,
        "data": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "total_points": rank_info["total_points"],
            "rank": {
                "id": rank_info["rank_id"],
                "name": rank_info["rank_name"],
                "avatar": rank_info["avatar"]
            }
        }
    }), 200


# Update profile (edit name, email, password)
@profile_bp.route('/', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Data cannot be empty"}), 400
    
    # Update name
    if 'name' in data and data['name']:
        user.name = data['name']
    
    # Update email (cek duplikat)
    if 'email' in data and data['email']:
        if data['email'] != user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing:
                return jsonify({"success": False, "message": "Email is already used by another account"}), 400
            user.email = data['email']
    
    # Update password (harus kirim old_password untuk verifikasi)
    if 'new_password' in data and data['new_password']:
        old_password = data.get('old_password')
        if not old_password:
            return jsonify({"success": False, "message": "Old password is required to change password"}), 400
        
        if not check_password_hash(user.password, old_password):
            return jsonify({"success": False, "message": "Old password is incorrect"}), 401
        
        user.password = generate_password_hash(data['new_password'])
    
    try:
        db.session.commit()
        
        notif = Notification(
            user_id=user_id,
            title="Profil Diperbarui",
            description="Data profil Anda telah berhasil diperbarui."
        )
        db.session.add(notif)
        db.session.commit()
        
        rank_info = get_user_rank(user_id)
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "total_points": rank_info["total_points"],
                "rank": {
                    "id": rank_info["rank_id"],
                    "name": rank_info["rank_name"],
                    "avatar": rank_info["avatar"]
                }
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
