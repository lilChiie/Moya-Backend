from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from api.extensions import db
from models.tourism import Tourism

tourism_bp = Blueprint('tourism', __name__)

# Get data tourism
@tourism_bp.route('/', methods=['GET'])
@jwt_required()
def get_all():
    items = Tourism.query.order_by(Tourism.created_at.desc()).all()
    return jsonify({"success": True, "data": [{"id": item.id, "name": item.name} for item in items]}), 200

@tourism_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_one(id):
    item = Tourism.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Tourism not found"}), 404
    return jsonify({"success": True, "data": {"id": item.id, "name": item.name}}), 200

# Create data tourism
@tourism_bp.route('/', methods=['POST'])
@jwt_required()
def create():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"success": False, "message": "Name is required"}), 400
        
    new_item = Tourism(name=data.get('name'))
    
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"success": True, "message": "Tourism created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Update data tourism
@tourism_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update(id):
    item = Tourism.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Tourism not found"}), 404
        
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"success": False, "message": "Name is required"}), 400
        
    item.name = data['name']
        
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Tourism updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Delete data tourism
@tourism_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    item = Tourism.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Tourism not found"}), 404
        
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Tourism deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
