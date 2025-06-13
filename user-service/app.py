import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Schema, Int, Field, List, Mutation, Boolean, Enum as GrapheneEnum
from models import db, User, UserRole
from seeders import seed_staff
import jwt
import datetime
import logging
import socket

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Konfigurasi database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'  # Secret key untuk JWT

db.init_app(app)

# GraphQL Schema
class UserRoleEnum(GrapheneEnum):
    class Meta:
        name = 'UserRole'
        description = 'User role enum'
        enum = UserRole

class UserType(ObjectType):
    id = Int()
    nama = String()
    email = String()
    role = String()
    created_at = String()
    updated_at = String()

class LoginResponse(ObjectType):
    user = Field(UserType)
    token = String()

class Query(ObjectType):
    all_users = List(UserType)
    user = Field(UserType, id=Int(required=True))
    staff_users = List(UserType)
    client_users = List(UserType)

    def resolve_all_users(self, info):
        return User.query.all()

    def resolve_user(self, info, id):
        return User.query.get(id)

    def resolve_staff_users(self, info):
        return User.query.filter_by(role=UserRole.STAFF.value).all()

    def resolve_client_users(self, info):
        return User.query.filter_by(role=UserRole.CLIENT.value).all()

class CreateUser(Mutation):
    class Arguments:
        nama = String(required=True)
        password = String(required=True)
        email = String(required=True)

    user = Field(UserType)

    def mutate(self, info, nama, password, email):
        # Check if user with given name or email already exists
        if User.query.filter_by(nama=nama).first():
            raise Exception('User with this name already exists')
        if User.query.filter_by(email=email).first():
            raise Exception('User with this email already exists')
            
        user = User(
            nama=nama,
            password=password,
            email=email,
            role=UserRole.CLIENT.value  # Default role is client
        )
        db.session.add(user)
        db.session.commit()
        return CreateUser(user=user)

class LoginUser(Mutation):
    class Arguments:
        nama = String(required=True)
        password = String(required=True)

    user = Field(UserType)
    token = String()

    def mutate(self, info, nama, password):
        user = User.query.filter_by(nama=nama).first()
        if user and user.password == password:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
            }, app.config['JWT_SECRET_KEY'])
            
            return LoginUser(user=user, token=token)
        raise Exception('Invalid credentials')

class UpdateUser(Mutation):
    class Arguments:
        id = Int(required=True)
        nama = String(required=True)
        password = String(required=True)

    user = Field(UserType)

    def mutate(self, info, id, nama, password):
        user = User.query.get(id)
        if user:
            user.nama = nama
            user.password = password
            db.session.commit()
        return UpdateUser(user=user)

class DeleteUser(Mutation):
    class Arguments:
        id = Int(required=True)

    success = Boolean()

    def mutate(self, info, id):
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return DeleteUser(success=True)
        return DeleteUser(success=False)

class DeleteAllUsers(Mutation):
    success = Boolean()

    def mutate(self, info):
        try:
            User.query.delete()
            db.session.commit()
            return DeleteAllUsers(success=True)
        except:
            return DeleteAllUsers(success=False)

class Mutation(ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()
    delete_all_users = DeleteAllUsers.Field()

schema = Schema(query=Query, mutation=Mutation)

# GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

# Test endpoint
@app.route('/test')
def test():
    return jsonify({"message": "Server is running!"})

# # Serve static files from the 'frontend' directory
# @app.route('/')
# def serve_index():
#     return send_from_directory(app.static_folder, 'index.html')

# @app.route('/<path:path>')
# def serve_static_files(path):
#     return send_from_directory(app.static_folder, path)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == '__main__':
    try:
        with app.app_context():
            # Hapus semua tabel dan buat ulang
            db.drop_all()
            db.create_all()
            seed_staff()  # Seed staff data
        
        if is_port_in_use(5003):
            logger.error("Port 5003 is already in use. Please close any other applications using this port.")
        else:
            logger.info("Starting server on port 5003...")
            app.run(host='127.0.0.1', port=5003, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}") 