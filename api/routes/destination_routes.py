from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from models.destination import Destination
from datetime import datetime, timedelta
from api.models import Itinerary, Review, UserPoint
from api.routes.profile_routes import get_user_rank
from api.routes.leaderboard_routes import get_rank_by_points
from models.notification import Notification
from sqlalchemy import func
from math import radians, cos, sin, asin, sqrt
from models.tourism import Tourism
from models.accessibility import Accessibility
from werkzeug.utils import secure_filename
import os
import json

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

destination_bp = Blueprint('destination', __name__)

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two coordinates using the Haversine formula."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    r = 6371000  # Earth's radius in meters
    return c * r

def check_duplicate_name_nearby(name, latitude, longitude, exclude_id=None):
    """Check if a destination with the same name exists within 500 meters."""
    if not latitude or not longitude:
        return False
    
    lat = float(latitude)
    lon = float(longitude)
    
    query = Destination.query.filter(Destination.name == name)
    if exclude_id:
        query = query.filter(Destination.id != exclude_id)
    
    same_name_destinations = query.all()
    
    for dest in same_name_destinations:
        if dest.latitude is not None and dest.longitude is not None:
            distance = haversine(lat, lon, float(dest.latitude), float(dest.longitude))
            if distance <= 500:
                return True
    return False

# Get data destination
@destination_bp.route('/', methods=['GET'])
@jwt_required()
def get_all():
    items = Destination.query.order_by(Destination.created_at.desc()).all()
    data_res = []
    for item in items:
        img_url = item.image_url
        if img_url and img_url.startswith('/static/'):
            img_url = f"{request.host_url.rstrip('/')}{img_url}"
            
        data_res.append({
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "image_url": img_url,
            "tourism_id": [t.id for t in item.tourisms],
            "accessibility_id": [a.id for a in item.accessibilities],
            "entrance_fee": float(item.entrance_fee) if item.entrance_fee is not None else None,
            "latitude": float(item.latitude) if item.latitude is not None else None,
            "longitude": float(item.longitude) if item.longitude is not None else None,
            "cleanliness_score": float(item.cleanliness_score) if item.cleanliness_score is not None else 0.5,
            "cleanliness_status": item.cleanliness_status
        })
    return jsonify({"success": True, "data": data_res}), 200

# Get user destination history based on itineraries
@destination_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    user_id = int(get_jwt_identity())
    
    itineraries = Itinerary.query.filter_by(user_id=user_id).order_by(Itinerary.created_at.desc()).all()
    
    data_res = []
    for it in itineraries:
        destinations = []
        
        # Urutkan berdasarkan urutan (sequence) kunjungan
        items = sorted(it.items, key=lambda x: x.sequence)
        
        for item in items:
            start_str = item.start_time.strftime("%H.%M") if item.start_time else ""
            end_str = ""
            
            if item.start_time and item.duration_minutes:
                # Hitung waktu selesai
                dummy_date = datetime.combine(datetime.today(), item.start_time)
                end_time = dummy_date + timedelta(minutes=item.duration_minutes)
                end_str = end_time.strftime("%H.%M")
                
            destinations.append({
                "sequence": item.sequence,
                "name": item.destination.name if item.destination else "Unknown",
                "start_time": start_str,
                "end_time": end_str
            })
            
        data_res.append({
            "itinerary_id": it.id,
            "name": it.name,
            "summary": {
                "total_destinations": len(items),
                "total_duration_minutes": it.total_duration,
                "total_cost": float(it.total_cost) if it.total_cost is not None else 0.0
            },
            "created_at": it.created_at.strftime("%Y-%m-%d %H:%M:%S") if it.created_at else None,
            "destinations": destinations
        })
        
    return jsonify({"success": True, "data": data_res}), 200

# Get latest 5 data tourism
@destination_bp.route('/latest', methods=['GET'])
@jwt_required()
def get_latest():
    items = Destination.query.order_by(Destination.created_at.desc()).limit(5).all()
    return jsonify({"success": True, "data": [{"id": item.id, "name": item.name} for item in items]}), 200

@destination_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_one(id):
    item = Destination.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Destination not found"}), 404
    data = item.to_dict()
    
    # Ambil data review untuk destinasi ini
    reviews = Review.query.filter_by(destination_id=id).order_by(Review.created_at.desc()).all()
    
    data['reviews'] = []
    for rev in reviews:
        # Dapatkan info rank user untuk mengambil avatar
        rank_info = get_user_rank(rev.user_id)
        
        data['reviews'].append({
            "id": rev.id,
            "user": {
                "id": rev.user.id,
                "name": rev.user.name,
                "avatar": rank_info.get('avatar')
            },
            "comment": rev.comment,
            "created_at": rev.created_at.strftime("%Y-%m-%d %H:%M:%S") if rev.created_at else None
        })
        
    return jsonify({"success": True, "data": data}), 200

# Add review for destination
@destination_bp.route('/<int:id>/add-review', methods=['POST'])
@jwt_required()
def add_review(id):
    item = Destination.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Destination not found"}), 404
        
    data = request.get_json()
    if not data or not data.get('comment'):
        return jsonify({"success": False, "message": "Comment is required"}), 400
        
    user_id = int(get_jwt_identity())
    
    # 1. Simpan review
    new_review = Review(
        user_id=user_id,
        destination_id=id,
        comment=data.get('comment')
    )
    db.session.add(new_review)
    db.session.flush() # Flush untuk mendapatkan new_review.id
    
    # 2. Tambah poin
    points_earned = 1
    new_point = UserPoint(
        user_id=user_id,
        review_id=new_review.id,
        points=points_earned
    )
    db.session.add(new_point)
    db.session.commit()
    
    # 3. Cek apakah user naik rank
    # Hitung total point sekarang
    total_points = db.session.query(
        func.coalesce(func.sum(UserPoint.points), 0)
    ).filter(UserPoint.user_id == user_id).scalar()
    
    total_points = int(total_points)
    
    # Bandingkan rank lama (sebelum dapat poin) dengan rank baru
    old_rank = get_rank_by_points(total_points - points_earned)
    new_rank = get_rank_by_points(total_points)
    
    # Jika id rank berbeda, berarti naik (atau turun, tapi dalam kasus ini pasti naik) rank
    if old_rank['id'] != new_rank['id'] and new_rank['name']:
        notif = Notification(
            user_id=user_id,
            title="Naik Rank! 🎉",
            description=f"Selamat! Kamu telah naik rank menjadi {new_rank['name']}. Terus tingkatkan kontribusimu!"
        )
        db.session.add(notif)
        db.session.commit()
        
    return jsonify({"success": True, "message": "Review added successfully"}), 201

# Create data destination
@destination_bp.route('/', methods=['POST'])
@jwt_required()
def create():
    data = request.form
    if not data or not data.get('name') or not data.get('tourism_id') or not data.get('accessibility_id'):
        return jsonify({"success": False, "message": "Name, tourism_id, and accessibility_id are required"}), 400
        
    image_url = None
    if 'image_url' in request.files:
        file = request.files['image_url']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({"success": False, "message": "Only JPG, JPEG, and PNG images are allowed"}), 400
                
            
            upload_folder = 'static/uploads/destinations'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            image_url = f"/static/uploads/destinations/{filename}"
    
    # Check duplicate name within 500 meters
    if check_duplicate_name_nearby(data.get('name'), data.get('latitude'), data.get('longitude')):
        return jsonify({"success": False, "message": "A destination with the same name already exists within 500 meters"}), 400
            
    try:
        new_item = Destination(
            name=data.get('name'),
            description=data.get('description'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            entrance_fee=data.get('entrance_fee', 0.00),
            estimated_duration=data.get('estimated_duration'),
            radius=data.get('radius'),
            image_url=image_url if image_url else data.get('image_url')
        )
        
        tourism_data = data.get('tourism_id')
        if tourism_data:
            try:
                t_ids = json.loads(tourism_data)
                if not isinstance(t_ids, list): t_ids = [t_ids]
            except:
                t_ids = [tourism_data]
            new_item.tourisms = Tourism.query.filter(Tourism.id.in_(t_ids)).all()
            
        acc_data = data.get('accessibility_id')
        if acc_data:
            try:
                a_ids = json.loads(acc_data)
                if not isinstance(a_ids, list): a_ids = [a_ids]
            except:
                a_ids = [acc_data]
            new_item.accessibilities = Accessibility.query.filter(Accessibility.id.in_(a_ids)).all()

        
        if data.get('opening_time'):
            new_item.opening_time = datetime.strptime(data['opening_time'], '%H:%M:%S').time()
        if data.get('closing_time'):
            new_item.closing_time = datetime.strptime(data['closing_time'], '%H:%M:%S').time()
            
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"success": True, "message": "Destination created successfully"}), 201
    except ValueError:
        return jsonify({"success": False, "message": "Invalid time format. Use HH:MM:SS"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Update data destination
@destination_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update(id):
    item = Destination.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Destination not found"}), 404
        
    data = request.form
    
    if 'tourism_id' in data: 
        try:
            t_ids = json.loads(data['tourism_id'])
            if not isinstance(t_ids, list): t_ids = [t_ids]
        except:
            t_ids = [data['tourism_id']]
        item.tourisms = Tourism.query.filter(Tourism.id.in_(t_ids)).all()
        
    if 'accessibility_id' in data: 
        try:
            a_ids = json.loads(data['accessibility_id'])
            if not isinstance(a_ids, list): a_ids = [a_ids]
        except:
            a_ids = [data['accessibility_id']]
        item.accessibilities = Accessibility.query.filter(Accessibility.id.in_(a_ids)).all()
    if 'name' in data: item.name = data['name']
    if 'description' in data: item.description = data['description']
    if 'latitude' in data: item.latitude = data['latitude']
    if 'longitude' in data: item.longitude = data['longitude']
    if 'entrance_fee' in data: item.entrance_fee = data['entrance_fee']
    if 'estimated_duration' in data: item.estimated_duration = data['estimated_duration']
    if 'radius' in data: item.radius = data['radius']
    
    # Check duplicate name within 500 meters (only if name/location changed)
    if 'name' in data or 'latitude' in data or 'longitude' in data:
        new_name = data.get('name', item.name)
        new_lat = data.get('latitude', item.latitude)
        new_lon = data.get('longitude', item.longitude)
        if check_duplicate_name_nearby(new_name, new_lat, new_lon, exclude_id=id):
            return jsonify({"success": False, "message": "A destination with the same name already exists within 500 meters"}), 400
    
    if 'image_url' in request.files:
        file = request.files['image_url']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({"success": False, "message": "Only JPG, JPEG, and PNG images are allowed"}), 400
                
            
            upload_folder = 'static/uploads/destinations'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            item.image_url = f"/static/uploads/destinations/{filename}"
    elif 'image_url' in data:
        item.image_url = data['image_url']
    
    try:
        if 'opening_time' in data and data['opening_time']: 
            item.opening_time = datetime.strptime(data['opening_time'], '%H:%M:%S').time()
        if 'closing_time' in data and data['closing_time']:
            item.closing_time = datetime.strptime(data['closing_time'], '%H:%M:%S').time()
            
        db.session.commit()
        return jsonify({"success": True, "message": "Destination updated successfully"}), 200
    except ValueError:
        return jsonify({"success": False, "message": "Invalid time format. Use HH:MM:SS"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Delete data destination
@destination_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    item = Destination.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Destination not found"}), 404
        
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Destination deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
