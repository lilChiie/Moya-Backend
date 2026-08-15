from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from api.extensions import db
from models.rank import Rank
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

rank_bp = Blueprint('rank', __name__)

# Get all data rank
@rank_bp.route('/', methods=['GET'])
@jwt_required()
def get_all():
    items = Rank.query.order_by(Rank.created_at.desc()).all()
    data = []
    for item in items:
        avatar_url = item.avatar
        if avatar_url and avatar_url.startswith('/static/'):
            avatar_url = f"{request.host_url.rstrip('/')}{avatar_url}"
            
        data.append({
            "id": item.id,
            "name": item.name,
            "min_point": item.min_point,
            "max_point": item.max_point,
            "avatar": avatar_url
        })
    return jsonify({"success": True, "data": data}), 200

# Create data rank
@rank_bp.route('/', methods=['POST'])
@jwt_required()
def create():
    data = request.form
    if not data or not data.get('name'):
        return jsonify({"success": False, "message": "Name is required"}), 400
        
    avatar_url = None
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({"success": False, "message": "Only JPG, JPEG, and PNG images are allowed"}), 400
                
            upload_folder = 'static/uploads/ranks'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            avatar_url = f"/static/uploads/ranks/{filename}"
            
    try:
        new_item = Rank(
            name=data.get('name'),
            min_point=data.get('min_point'),
            max_point=data.get('max_point'),
            avatar=avatar_url if avatar_url else data.get('avatar')
        )
        
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"success": True, "message": "Rank created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Update data rank
@rank_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update(id):
    item = Rank.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Rank not found"}), 404
        
    data = request.form
    
    if 'name' in data: item.name = data['name']
    if 'min_point' in data: item.min_point = data['min_point']
    if 'max_point' in data: item.max_point = data['max_point']
    
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename != '':
            if not allowed_file(file.filename):
                return jsonify({"success": False, "message": "Only JPG, JPEG, and PNG images are allowed"}), 400
                
            upload_folder = 'static/uploads/ranks'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            filename = secure_filename(file.filename)
            file.save(os.path.join(upload_folder, filename))
            item.avatar = f"/static/uploads/ranks/{filename}"
    elif 'avatar' in data:
        item.avatar = data['avatar']
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Rank updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Delete data rank
@rank_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    item = Rank.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Rank not found"}), 404
        
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Rank deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
