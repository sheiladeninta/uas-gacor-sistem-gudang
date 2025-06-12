import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from models import User
from flask_jwt_extended import jwt_required, get_jwt_identity

# Type definitions
class UserType(SQLAlchemyObjectType):
    class Meta:
        model = User
        interfaces = (graphene.relay.Node,)
        exclude_fields = ('password_hash',)

# Query definitions
class Query(graphene.ObjectType):
    # User queries
    users = graphene.List(UserType)
    user = graphene.Field(UserType, id=graphene.ID())
    me = graphene.Field(UserType)

    def resolve_users(self, info):
        return User.query.all()

    def resolve_user(self, info, id):
        return User.query.get(id)

    @jwt_required()
    def resolve_me(self, info):
        current_user_id = get_jwt_identity()
        return User.query.get(current_user_id)

# Mutation definitions
class CreateUser(graphene.Mutation):
    class Arguments:
        nama = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(UserType)

    def mutate(self, info, nama, password):
        user = User(nama=nama)
        user.set_password(password)
        
        from app import db
        db.session.add(user)
        db.session.commit()
        
        return CreateUser(user=user)

class UpdateUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        nama = graphene.String()
        password = graphene.String()

    user = graphene.Field(UserType)

    @jwt_required()
    def mutate(self, info, id, **kwargs):
        user = User.query.get(id)
        if not user:
            raise Exception('User not found')
        
        if 'nama' in kwargs and kwargs['nama'] is not None:
            user.nama = kwargs['nama']
        
        if 'password' in kwargs and kwargs['password'] is not None:
            user.set_password(kwargs['password'])
        
        from app import db
        db.session.commit()
        
        return UpdateUser(user=user)

class DeleteUser(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @jwt_required()
    def mutate(self, info, id):
        user = User.query.get(id)
        if not user:
            raise Exception('User not found')
        
        from app import db
        db.session.delete(user)
        db.session.commit()
        
        return DeleteUser(success=True)

class Mutation(graphene.ObjectType):
    create_user = CreateUser.Field()
    update_user = UpdateUser.Field()
    delete_user = DeleteUser.Field()

# Create schema
schema = graphene.Schema(query=Query, mutation=Mutation) 