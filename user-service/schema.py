from graphene import ObjectType, String, Int, List, Schema, Field, Mutation, InputObjectType
from graphene_sqlalchemy import SQLAlchemyObjectType
from models import User, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from graphql import GraphQLError

class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User
        # Hanya tampilkan field yang aman
        only_fields = ('user_id', 'nama', 'created_at')
        # Konversi nama field ke camelCase
        convert_choices_to_enum = False
        # Tetap gunakan snake_case untuk nama field
        use_enum_values = True

class UserInput(InputObjectType):
    userId = Int(required=True)
    nama = String(required=True)
    password = String(required=True)

class CreateUser(Mutation):
    class Arguments:
        userData = UserInput(required=True)

    user = Field(UserType)
    message = String()

    def mutate(self, info, userData):
        try:
            # Validasi input
            if not userData.userId or not userData.nama or not userData.password:
                raise GraphQLError("Semua field harus diisi")

            # Cek apakah user_id sudah terdaftar
            if User.query.filter_by(user_id=userData.userId).first():
                raise GraphQLError("User ID sudah terdaftar")

            # Buat user baru
            new_user = User(
                user_id=userData.userId,
                nama=userData.nama,
                password=generate_password_hash(userData.password)
            )
            
            db.session.add(new_user)
            db.session.commit()
            return CreateUser(user=new_user, message="User berhasil dibuat")
        except GraphQLError as e:
            db.session.rollback()
            return CreateUser(message=str(e))
        except Exception as e:
            db.session.rollback()
            return CreateUser(message=f"Terjadi kesalahan: {str(e)}")

class LoginUser(Mutation):
    class Arguments:
        userId = Int(required=True)
        password = String(required=True)

    token = String()
    message = String()
    user = Field(UserType)

    def mutate(self, info, userId, password):
        try:
            if not userId or not password:
                raise GraphQLError("User ID dan password diperlukan")

            user = User.query.filter_by(user_id=userId).first()
            
            if not user:
                raise GraphQLError("User ID tidak ditemukan")
            
            if not check_password_hash(user.password, password):
                raise GraphQLError("Password salah")

            access_token = create_access_token(
                identity={'user_id': user.user_id, 'nama': user.nama}
            )
            return LoginUser(
                token=access_token,
                message="Login berhasil",
                user=user
            )
        except GraphQLError as e:
            return LoginUser(message=str(e))
        except Exception as e:
            return LoginUser(message=f"Terjadi kesalahan: {str(e)}")

class Query(ObjectType):
    # Query untuk mendapatkan semua user
    users = List(UserType)
    
    # Query untuk mendapatkan user berdasarkan ID
    user = Field(UserType, userId=Int(required=True))
    
    def resolve_users(self, info):
        try:
            return User.query.all()
        except Exception as e:
            raise GraphQLError(f"Gagal mengambil data users: {str(e)}")
    
    def resolve_user(self, info, userId):
        try:
            user = User.query.get(userId)
            if not user:
                raise GraphQLError(f"User dengan ID {userId} tidak ditemukan")
            return user
        except GraphQLError as e:
            raise e
        except Exception as e:
            raise GraphQLError(f"Gagal mengambil data user: {str(e)}")

class Mutation(ObjectType):
    create_user = CreateUser.Field()
    login_user = LoginUser.Field()

schema = Schema(query=Query, mutation=Mutation) 