import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from datetime import datetime
from graphene import ObjectType, String, Int, Boolean, Field, List, Mutation, Schema
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import requests
from graphene import ObjectType, String, Int, Boolean, Field, List, Mutation  # Pastikan Boolean diimpor
import os
from models import db, InventoryItem, InventoryLog, InventoryStatus  # Import models dari models.py

# Initialize the Flask app
app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Inisialisasi Migrate
migrate = Migrate(app, db)

# Database Configuration
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'inventory-service.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory-service.db' 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize the database with Flask
db.init_app(app)


# GraphQL Schema for Inventory Service
class InventoryItemType(ObjectType):
    id = Int()
    item_code = String(required=True)
    name = String()
    quantity = Int()
    description = String()
    unit = String()
    min_stor = Int()
    location = String()

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

# Menambahkan LogisticRequestType
class LogisticRequestType(ObjectType):
    id = Int()
    item_id = Int()
    quantity = Int()
    reference = String()
    status = String()
    created_at = String()


# Query untuk Inventory dan Logistic
class Query(ObjectType):
    # Query untuk inventory
    allInventory = List(InventoryItemType)
    inventoryItem = Field(InventoryItemType, id=Int(), itemCode=String())  # Perbaiki: Handle id dan itemCode
    allInventoryLogs = List(InventoryLogType)
    inventoryStatus = Field(InventoryStatusType, item_id=Int(required=True))
    
    # Query untuk logistic requests
    allLogisticRequests = List(LogisticRequestType)
    logisticRequest = Field(LogisticRequestType, id=Int(required=True))

    def resolve_allInventory(self, info):
        return InventoryItem.query.all()  # Mengambil semua inventory item

    def resolve_inventoryItem(self, info, id=None, itemCode=None):  # Perbaiki: Handle id dan itemCode
        if itemCode:
            return InventoryItem.query.filter_by(item_code=itemCode).first()  # Cari berdasarkan itemCode
        if id:
            return InventoryItem.query.get(id)  # Cari berdasarkan ID jika ada
        return None  # Jika tidak ada parameter yang diberikan, kembalikan None

    def resolve_allInventoryLogs(self, info):
        return InventoryLog.query.all()  # Mengambil semua log transaksi inventaris

    def resolve_inventoryStatus(self, info, item_id):
        return InventoryStatus.query.filter_by(item_id=item_id).first()  # Mengambil status inventaris berdasarkan item_id
    
    # Resolver untuk LogisticRequest
    def resolve_allLogisticRequests(self, info):
        logistic_service_url = 'http://localhost:5002/graphql'  # Ganti dengan URL `logistic-service`
        query = '''
        query {
            all_logistic_requests {
                id
                itemId
                quantity
                reference
                status
                createdAt
            }
        }
        '''
        try:
            response = requests.post(logistic_service_url, json={'query': query})
            response.raise_for_status()
            return response.json()['data']['all_logistic_requests']
        except requests.exceptions.RequestException as e:
            print(f"Error fetching logistic requests: {e}")
            return []

    def resolve_logisticRequest(self, info, id):
        logistic_service_url = 'http://localhost:5002/graphql'  # Ganti dengan URL `logistic-service`
        query = f'''
        query {{
            logistic_request(id: {id}) {{
                id
                itemId
                quantity
                reference
                status
                createdAt
            }}
        }}
        '''
        try:
            response = requests.post(logistic_service_url, json={'query': query})
            response.raise_for_status()
            return response.json()['data']['logistic_request']
        except requests.exceptions.RequestException as e:
            print(f"Error fetching logistic request with ID {id}: {e}")
            return None


# Mutation untuk Inventory
class CreateInventoryItem(Mutation):
    class Arguments:
        itemCode = String(required=True)
        name = String(required=True)
        quantity = Int(required=True)
        description = String()
        unit = String()
        minStor = Int()
        location = String()

    inventoryItem = Field(InventoryItemType)

    def mutate(self, info, itemCode, name, quantity, description=None, unit=None, minStor=None, location=None):
        item = InventoryItem(
            item_code=itemCode, 
            name=name, 
            quantity=quantity, 
            description=description, 
            unit=unit, 
            min_stor=minStor, 
            location=location
        )
        db.session.add(item)
        db.session.commit()  # Commit untuk menyimpan item dan mendapatkan ID

        inventoryStatus = InventoryStatus(
            item_id=item.id,
            current_stock=quantity,
            last_updated=datetime.utcnow()
        )
        db.session.add(inventoryStatus)
        db.session.commit()  # Commit untuk menyimpan status inventaris

        return CreateInventoryItem(inventoryItem=item)


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

class UpdateInventoryItem(Mutation):
    class Arguments:
        id = Int(required=True)
        name = String()
        quantity = Int()
        description = String()
        unit = String()
        minStor = Int()
        location = String()

    inventoryItem = Field(InventoryItemType)

    def mutate(self, info, id, name=None, quantity=None, description=None, unit=None, minStor=None, location=None):
        item = InventoryItem.query.get(id)
        if item:
            if name: item.name = name
            if quantity: item.quantity = quantity
            if description: item.description = description
            if unit: item.unit = unit
            if minStor: item.min_stor = minStor
            if location: item.location = location
            
            db.session.commit()
            return UpdateInventoryItem(inventoryItem=item)
        else:
            raise Exception("Item not found")

class DeleteInventoryItem(Mutation):
    class Arguments:
        id = Int(required=True)

    success = Boolean()  # Pastikan Boolean diimpor dan digunakan dengan benar

    def mutate(self, info, id):
        item = InventoryItem.query.get(id)
        if item:
            db.session.delete(item)
            db.session.commit()
            return DeleteInventoryItem(success=True)
        else:
            raise Exception("Item not found")


# Menambahkan Mutation
class Mutation(ObjectType):
    create_inventory_item = CreateInventoryItem.Field()
    create_inventory_log = CreateInventoryLog.Field()

# Create GraphQL Schema
schema = Schema(query=Query, mutation=Mutation)

# Add GraphQL endpoint
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

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory(app.static_folder, path)

# Create all tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)
