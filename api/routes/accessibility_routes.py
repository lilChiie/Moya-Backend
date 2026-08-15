from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from api.extensions import db
from models.accessibility import Accessibility

accessibility_bp = Blueprint('accessibility', __name__)

# Get data accessibility
@accessibility_bp.route('/', methods=['GET'])
@jwt_required()
def get_all():
    items = Accessibility.query.order_by(Accessibility.created_at.desc()).all()
    return jsonify({"success": True, "data": [item.to_dict() for item in items]}), 200

@accessibility_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_one(id):
    item = Accessibility.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Accessibility not found"}), 404
    return jsonify({"success": True, "data": item.to_dict()}), 200

# Create data accessibility
@accessibility_bp.route('/', methods=['POST'])
@jwt_required()
def create():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"success": False, "message": "Name is required"}), 400
        
    new_item = Accessibility(name=data.get('name'))
    
    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"success": True, "message": "Accessibility created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Update data accessibility
@accessibility_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update(id):
    item = Accessibility.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Accessibility not found"}), 404
        
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"success": False, "message": "Name is required"}), 400
        
    item.name = data['name']
        
    try:
        db.session.commit()
        return jsonify({"success": True, "message": "Accessibility updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

# Delete data accessibility
@accessibility_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete(id):
    item = Accessibility.query.get(id)
    if not item:
        return jsonify({"success": False, "message": "Accessibility not found"}), 404
        
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Accessibility deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500
