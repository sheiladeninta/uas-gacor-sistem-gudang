from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Schema, Int, Field, List, Mutation, Boolean
from models import db, InventoryItem
import os

# Initialize the Flask app
app = Flask(__name__, static_folder='../frontend')  # Adjust the static folder path
CORS(app)  # Allow all origins (you can adjust this as needed)

# Database Configuration
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'inventory-service.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # Absolute path to the DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable tracking of modifications
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize the database with Flask
db.init_app(app)

# GraphQL Schema
class InventoryItemType(ObjectType):
    id = Int()
    name = String()
    quantity = Int()
    description = String()

class Query(ObjectType):
    all_inventory = List(InventoryItemType)  # Get all items
    inventory_item = Field(InventoryItemType, id=Int(required=True))  # Get item by ID

    def resolve_all_inventory(self, info):
        return InventoryItem.query.all()  # Get all items from the database

    def resolve_inventory_item(self, info, id):
        return InventoryItem.query.get(id)  # Get a specific item by ID

class CreateInventoryItem(Mutation):
    class Arguments:
        name = String(required=True)
        quantity = Int(required=True)
        description = String()

    inventory_item = Field(InventoryItemType)

    def mutate(self, info, name, quantity, description=None):
        item = InventoryItem(name=name, quantity=quantity, description=description)
        db.session.add(item)
        db.session.commit()
        return CreateInventoryItem(inventory_item=item)

class UpdateInventoryItem(Mutation):
    class Arguments:
        id = Int(required=True)
        name = String()
        quantity = Int()
        description = String()

    inventory_item = Field(InventoryItemType)

    def mutate(self, info, id, name=None, quantity=None, description=None):
        item = InventoryItem.query.get(id)
        if item:
            if name:
                item.name = name
            if quantity:
                item.quantity = quantity
            if description:
                item.description = description
            db.session.commit()
            return UpdateInventoryItem(inventory_item=item)
        return UpdateInventoryItem(inventory_item=None)

class DeleteInventoryItem(Mutation):
    class Arguments:
        id = Int(required=True)

    success = Boolean()

    def mutate(self, info, id):
        item = InventoryItem.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return DeleteInventoryItem(success=True)
        return DeleteInventoryItem(success=False)

class Mutation(ObjectType):
    create_inventory_item = CreateInventoryItem.Field()
    update_inventory_item = UpdateInventoryItem.Field()
    delete_inventory_item = DeleteInventoryItem.Field()

schema = Schema(query=Query, mutation=Mutation)

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphiQL interface
    )
)

# API for testing if the server is running
@app.route('/test')
def test():
    return jsonify({"message": "Server is running!"})

# Serve static files from the 'frontend' directory
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    # Initialize the database schema
    with app.app_context():
        db.create_all()  # Ensure that the tables are created

    # Start the Flask application
    app.run(host='0.0.0.0', port=5003, debug=True)
