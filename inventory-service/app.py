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
    allInventory = List(InventoryItemType)
    inventoryItem = Field(InventoryItemType, id=Int(required=True))
    allInventoryLogs = List(InventoryLogType)
    inventoryStatus = Field(InventoryStatusType, item_id=Int(required=True))

    def resolve_allInventory(self, info):
        return InventoryItem.query.all()

    def resolve_inventoryItem(self, info, id):
        return InventoryItem.query.get(id)

    def resolve_allInventoryLogs(self, info):
        return InventoryLog.query.all()

    def resolve_inventoryStatus(self, info, item_id):
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

# Endpoint untuk inbound inventory (barang masuk)
@app.route('/inventory/inbound', methods=['POST'])
def inbound_inventory():
    data = request.get_json()

    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')
    created_by = data.get('created_by')

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

# Endpoint untuk outbound inventory (barang keluar)
@app.route('/inventory/outbound', methods=['POST'])
def outbound_inventory():
    data = request.get_json()

    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')
    created_by = data.get('created_by')

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


# Endpoint untuk menambahkan item
@app.route('/api/inventory', methods=['POST'])
def add_inventory_item():
    data = request.get_json()
    new_item = InventoryItem(
        item_code=data['item_code'],
        name=data['name'],
        quantity=data['quantity'],
        description=data['description'],
        unit=data['unit'],
        min_stor=data['min_stor'],
        location=data['location']
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Item added successfully!"}), 201

# Endpoint untuk mendapatkan semua item inventory
@app.route('/api/inventory', methods=['GET', 'POST'])
def manage_inventory():
    if request.method == 'GET':
        # Mengambil semua item dari database dan mengonversinya ke format JSON menggunakan serialize()
        items = InventoryItem.query.all()
        return jsonify([item.serialize() for item in items])  # Gunakan serialize() untuk mengubah objek menjadi JSON
    
    if request.method == 'POST':
        data = request.get_json()
        new_item = InventoryItem(
            item_code=data['item_code'],
            name=data['name'],
            quantity=data['quantity'],
            description=data['description'],
            unit=data['unit'],
            min_stor=data['min_stor'],
            location=data['location']
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.serialize()), 201


# Endpoint untuk memperbarui item
@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    data = request.get_json()
    item.quantity = data['quantity']
    db.session.commit()
    return jsonify(item.serialize())

# Endpoint untuk mendapatkan semua logs inventory
@app.route('/api/inventory/logs', methods=['GET'])
def get_inventory_logs():
    logs = InventoryLog.query.all()
    return jsonify([log.serialize() for log in logs])  # Menggunakan serialize() pada model InventoryLog

# Endpoint untuk mendapatkan semua status inventory
@app.route('/api/inventory/status', methods=['GET'])
def get_inventory_status():
    status = InventoryStatus.query.all()
    return jsonify([status_item.serialize() for status_item in status])  # Menggunakan serialize() pada model InventoryStatus

# Endpoint untuk menerima request barang dari logistic service
@app.route('/api/inventory/request', methods=['POST'])
def request_inventory():
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')
    created_by = data.get('created_by')  # ID of the user creating the request

    # Cek apakah item tersedia
    item = InventoryItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404

    # Membuat log permintaan
    log = InventoryLog(
        item_id=item_id,
        log_type='request',  # Menandakan bahwa ini adalah permintaan
        quantity=quantity,
        reference=reference,
        created_by=created_by,
        created_at=datetime.utcnow(),
        status='pending'  # Status awal adalah pending
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Request submitted successfully!", "log_id": log.log_id}), 201

# Endpoint untuk approve request barang
@app.route('/api/inventory/approve', methods=['POST'])
def approve_inventory_request():
    data = request.get_json()
    log_id = data.get('log_id')
    approved_quantity = data.get('approved_quantity')

    if approved_quantity <= 0:
        return jsonify({"error": "Approved quantity must be greater than zero"}), 400

    # Mencari log yang sesuai
    log = InventoryLog.query.get(log_id)
    if not log:
        return jsonify({"error": "Log not found"}), 404

    if log.status != 'pending':
        return jsonify({"error": "Request already processed"}), 400

    # Memperbarui status log menjadi approved
    log.status = 'approved'

    # Update inventory status
    inventory_status = InventoryStatus.query.get(log.item_id)
    if inventory_status:
        if inventory_status.current_stock >= approved_quantity:
            # Update stok barang
            inventory_status.current_stock -= approved_quantity
            inventory_status.last_updated = datetime.utcnow()

            # Menambahkan log outbound (pengiriman barang)
            outbound_log = InventoryLog(
                item_id=log.item_id,
                log_type='outbound',
                quantity=approved_quantity,
                reference=log.reference,
                created_by=log.created_by,
                created_at=datetime.utcnow(),
                status='approved'
            )
            db.session.add(outbound_log)

            # Commit semua perubahan dalam satu batch
            db.session.commit()

            return jsonify({"message": "Request approved and inventory updated"}), 200
        else:
            return jsonify({"error": "Insufficient stock"}), 400
    else:
        return jsonify({"error": "Inventory status not found"}), 404


# Create all tables if they don't exist
with app.app_context():
    db.create_all()  # Ensure that the tables are created

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
