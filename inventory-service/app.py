import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Schema, Int, Field, List, Mutation, Boolean
from models import db, InventoryItem, InventoryLog, InventoryStatus
from datetime import datetime
import requests
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

# GraphQL Schema for Inventory Service
class InventoryItemType(ObjectType):
    id = Int()
    item_code = String(required=True)  # Tambahkan item_code
    name = String()
    quantity = Int()
    description = String()
    unit = String()  # Tambahkan unit
    min_stor = Int()  # Tambahkan min_stor
    location = String()  # Tambahkan location

class InventoryLogType(ObjectType):
    id = Int()
    item_id = Int()
    log_type = String()
    quantity = Int()
    reference = String()
    created_by = Int()
    created_at = String()

class InventoryStatusType(ObjectType):
    item_id = Int()
    current_stock = Int()
    last_updated = String()

class Query(ObjectType):
    all_inventory = List(InventoryItemType)
    inventory_item = Field(InventoryItemType, id=Int(required=True))
    all_inventory_logs = List(InventoryLogType)
    inventory_status = Field(InventoryStatusType, item_id=Int(required=True))

    def resolve_all_inventory(self, info):
        return InventoryItem.query.all()

    def resolve_inventory_item(self, info, id):
        return InventoryItem.query.get(id)

    def resolve_all_inventory_logs(self, info):
        return InventoryLog.query.all()

    def resolve_inventory_status(self, info, item_id):
        return InventoryStatus.query.filter_by(item_id=item_id).first()


# app.py

class CreateInventoryItem(Mutation):
    class Arguments:
        item_code = String(required=True)  # Item code
        name = String(required=True)
        quantity = Int(required=True)
        description = String()
        unit = String()
        min_stor = Int()
        location = String()

    inventory_item = Field(InventoryItemType)

    def mutate(self, info, item_code, name, quantity, description=None, unit=None, min_stor=None, location=None):
        # Inisialisasi objek InventoryItem dengan argumen yang diperlukan
        item = InventoryItem(
            item_code=item_code,  # Pastikan item_code ada
            name=name,
            quantity=quantity,
            description=description,
            unit=unit,
            min_stor=min_stor,
            location=location
        )
        db.session.add(item)
        db.session.commit()
        
        # Return the created InventoryItem in the mutation result
        return CreateInventoryItem(inventory_item=item)  # Return the item

class CreateInventoryLog(Mutation):
    class Arguments:
        item_id = Int(required=True)
        log_type = String(required=True)
        quantity = Int(required=True)
        reference = String()
        created_by = Int(required=True)

    inventory_log = Field(InventoryLogType)

    def mutate(self, info, item_id, log_type, quantity, reference, created_by):
        log = InventoryLog(
            item_id=item_id,
            log_type=log_type,
            quantity=quantity,
            reference=reference,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        return CreateInventoryLog(inventory_log=log)

class Mutation(ObjectType):
    create_inventory_item = CreateInventoryItem.Field()
    create_inventory_log = CreateInventoryLog.Field()

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

@app.route('/inventory/inbound', methods=['POST'])
def inbound_inventory():
    data = request.get_json()

    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')
    created_by = data.get('created_by')

    # Cek jika item_id valid
    item = InventoryItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Update inventory_status
    inventory_status = InventoryStatus.query.filter_by(item_id=item_id).first()
    if inventory_status:
        inventory_status.current_stock += quantity
        inventory_status.last_updated = datetime.utcnow()
    else:
        inventory_status = InventoryStatus(item_id=item_id, current_stock=quantity, last_updated=datetime.utcnow())
        db.session.add(inventory_status)

    # Log transaksi inbound
    log = InventoryLog(
        item_id=item_id, 
        log_type='inbound', 
        quantity=quantity, 
        reference=reference, 
        created_by=created_by, 
        created_at=datetime.utcnow()
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Inventory updated successfully"}), 200


@app.route('/inventory/outbound', methods=['POST'])
def outbound_inventory():
    data = request.get_json()

    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')
    created_by = data.get('created_by')

    # Cek jika item_id valid
    item = InventoryItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Update inventory_status
    inventory_status = InventoryStatus.query.filter_by(item_id=item_id).first()
    if inventory_status and inventory_status.current_stock >= quantity:
        inventory_status.current_stock -= quantity
        inventory_status.last_updated = datetime.utcnow()
    else:
        return jsonify({"error": "Insufficient stock"}), 400

    # Log transaksi outbound
    log = InventoryLog(
        item_id=item_id, 
        log_type='outbound', 
        quantity=quantity, 
        reference=reference, 
        created_by=created_by, 
        created_at=datetime.utcnow()
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Inventory updated successfully"}), 200

# Create all tables if they don't exist
with app.app_context():
    db.create_all()  # Ensure that the tables are created

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
