from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User
from schema import schema
from graphene import Schema
from flask_graphql import GraphQLView
from datetime import timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/sistem_gudang'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Konfigurasi JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

# Inisialisasi ekstensi
db.init_app(app)
jwt = JWTManager(app)

# Tambahkan endpoint GraphQL
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Untuk GraphiQL interface
    )
)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validasi input
    if not all(k in data for k in ('user_id', 'nama', 'password')):
        return jsonify({'error': 'Data tidak lengkap'}), 400
    
    # Cek apakah user_id sudah terdaftar
    if User.query.filter_by(user_id=data['user_id']).first():
        return jsonify({'error': 'User ID sudah terdaftar'}), 400
    
    # Buat user baru
    new_user = User(
        user_id=data['user_id'],
        nama=data['nama'],
        password=data['password']
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User berhasil dibuat'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validasi input
    if not all(k in data for k in ('user_id', 'password')):
        return jsonify({'error': 'User ID dan password diperlukan'}), 400
    
    user = User.query.filter_by(user_id=data['user_id']).first()
    
    if not user or user.password != data['password']:
        return jsonify({'error': 'User ID atau password salah'}), 401
    
    # Buat token
    access_token = create_access_token(
        identity={'user_id': user.user_id, 'nama': user.nama}
    )
    
    return jsonify({
        'token': access_token,
        'user': {
            'user_id': user.user_id,
            'nama': user.nama
        }
    }), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    user = User.query.filter_by(user_id=current_user['user_id']).first()
    
    if not user:
        return jsonify({'error': 'User tidak ditemukan'}), 404
    
    return jsonify({
        'user_id': user.user_id,
        'nama': user.nama
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Buat tabel jika belum ada
    app.run(debug=True, port=5001)
