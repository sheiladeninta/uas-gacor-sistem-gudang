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
import os

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:8000", "http://127.0.0.1:8000"]}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Konfigurasi database
instance_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
os.makedirs(instance_folder, exist_ok=True)
db_path = os.path.join(instance_folder, 'user-service.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-key'

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
    username = String()
    email = String()
    companyName = String()  # Changed from company_name to companyName
    role = String()
    createdAt = String()    # Changed from created_at to createdAt
    updatedAt = String()    # Changed from updated_at to updatedAt
    
    # Resolver methods to map from database fields to GraphQL fields
    def resolve_companyName(self, info):
        return self.companyName
    
    def resolve_createdAt(self, info):
        return str(self.created_at) if hasattr(self, 'created_at') and self.created_at else None
    
    def resolve_updatedAt(self, info):
        return str(self.updated_at) if hasattr(self, 'updated_at') and self.updated_at else None

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
        nama = String()
        username = String()
        password = String(required=True)
        email = String(required=True)
        companyName = String()  # Changed from company_name to companyName
        role = String()

    user = Field(UserType)

    def mutate(self, info, password, email, nama=None, username=None, companyName=None, role=None):
        # Validasi role
        if role and role not in [UserRole.STAFF.value, UserRole.CLIENT.value]:
            raise Exception('Invalid role')
        
        user_role = role or UserRole.CLIENT.value
        
        # Untuk CLIENT, username dan companyName wajib
        if user_role == UserRole.CLIENT.value:
            if not username:
                raise Exception('Username is required for client registration')
            if not companyName:
                raise Exception('Company name is required for client registration')
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                raise Exception('Username already exists')
            
            # Untuk client, gunakan companyName sebagai nama jika nama tidak disediakan
            if not nama:
                nama = companyName
        
        # Untuk STAFF, nama wajib
        if user_role == UserRole.STAFF.value:
            if not nama:
                raise Exception('Nama is required for staff registration')
            
            # Check if nama already exists for staff
            if User.query.filter_by(nama=nama, role=UserRole.STAFF.value).first():
                raise Exception('Staff with this name already exists')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            raise Exception('Email already exists')
            
        user = User(
            nama=nama,
            username=username,
            password=password,
            email=email,
            companyName=companyName,  # Map companyName to company_name for database
            role=user_role
        )
        db.session.add(user)
        db.session.commit()
        return CreateUser(user=user)

class CreateClientUser(Mutation):
    """Mutation khusus untuk registrasi client dari frontend"""
    class Arguments:
        username = String(required=True)
        password = String(required=True)
        email = String(required=True)
        companyName = String(required=True)  # Changed from company_name to companyName

    user = Field(UserType)

    def mutate(self, info, username, password, email, companyName):
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            raise Exception('Username already exists')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            raise Exception('Email already exists')
        
        # Untuk client, gunakan companyName sebagai nama
        user = User(
            nama=companyName,  # Gunakan companyName sebagai nama
            username=username,
            password=password,
            email=email,
            companyName=companyName,  # Map companyName to company_name for database
            role=UserRole.CLIENT.value
        )
        db.session.add(user)
        db.session.commit()
        return CreateClientUser(user=user)

class LoginUser(Mutation):
    class Arguments:
        identifier = String(required=True)
        password = String(required=True)

    user = Field(UserType)
    token = String()

    def mutate(self, info, identifier, password):
        # Coba cari berdasarkan nama (untuk staff) atau username (untuk client)
        user = User.query.filter(
            (User.nama == identifier) | (User.username == identifier)
        ).first()
        
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
        nama = String()
        username = String()
        password = String()
        email = String()
        companyName = String()  # Changed from company_name to companyName

    user = Field(UserType)

    def mutate(self, info, id, nama=None, username=None, password=None, email=None, companyName=None):
        user = User.query.get(id)
        if not user:
            raise Exception('User not found')
        
        if nama:
            user.nama = nama
        if username:
            # Check if username already exists for other users
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != id:
                raise Exception('Username already exists')
            user.username = username
        if password:
            user.password = password
        if email:
            # Check if email already exists for other users
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != id:
                raise Exception('Email already exists')
            user.email = email
        if companyName:
            user.companyName = companyName  # Map companyName to company_name for database
            # Untuk client, update nama juga jika companyName berubah
            if user.role == UserRole.CLIENT.value:
                user.nama = companyName
            
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
    create_client_user = CreateClientUser.Field()
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

@app.route('/test')
def test():
    return jsonify({"message": "Server is running!"})

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 5003

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