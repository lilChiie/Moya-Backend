from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from api.extensions import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Data cannot be empty"}), 400
        
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify({"success": False, "message": "Name, email, and password are required"}), 400
        
    # Cek apakah email sudah terdaftar di database
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "message": "Email is already registered"}), 400
        
    # Hash password sebelum disimpan
    hashed_password = generate_password_hash(password)
    
    # Buat instance User baru
    new_user = User(name=name, email=email, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Registration successful"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "message": "Data tidak boleh kosong"}), 400
        
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400
        
    # Cari user berdasarkan email
    user = User.query.filter_by(email=email).first()
    
    # Verifikasi password dengan hash yang ada di db
    if not user or not check_password_hash(user.password, password):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401
        
    # Generate JWT token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "success": True, 
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }), 200
