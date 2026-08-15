from flask import Blueprint, request, jsonify
from api.extensions import db
from api.models import UserPoint
from models.user import User
from models.rank import Rank
from sqlalchemy import func

leaderboard_bp = Blueprint('leaderboard', __name__)

def get_rank_by_points(total_points):
    """Mencari rank yang sesuai berdasarkan total points."""
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
        "id": rank.id if rank else None,
        "name": rank.name if rank else None,
        "avatar": avatar_url
    }

@leaderboard_bp.route('/', methods=['GET'])
def get_leaderboard():
    # Ambil 10 user dengan total poin tertinggi
    users_with_points = db.session.query(
        User.id,
        User.name,
        func.coalesce(func.sum(UserPoint.points), 0).label('total_points')
    ).outerjoin(UserPoint, User.id == UserPoint.user_id) \
     .filter(User.role == 'user') \
     .group_by(User.id) \
     .order_by(func.coalesce(func.sum(UserPoint.points), 0).desc()) \
     .limit(10).all()
    
    leaderboard_data = []
    for user_record in users_with_points:
        total_points = int(user_record.total_points)
        rank_info = get_rank_by_points(total_points)
        
        leaderboard_data.append({
            "id": user_record.id,
            "name": user_record.name,
            "total_points": total_points,
            "rank": rank_info
        })
        
    return jsonify({
        "success": True,
        "data": leaderboard_data
    }), 200
