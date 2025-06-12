import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from datetime import datetime
from graphene import ObjectType, String, Int, Field, List, Mutation, Schema
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from models import db, Item, Order, LogisticRequest

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'logistic-management.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# GraphQL Schema for Logistic Service
class ItemType(ObjectType):
    itemId = Int()
    itemCode = String()
    name = String()
    description = String()
    unit = String()
    minStor = Int()
    location = String()

class OrderType(ObjectType):
    orderId = Int()
    itemId = Int()
    quantity = Int()
    reference = String()
    status = String()
    createdAt = String()
    item = Field(ItemType)

class LogisticRequestType(ObjectType):
    id = Int()
    itemId = Int()
    quantity = Int()
    reference = String()
    createdBy = Int()
    status = String()
    createdAt = String()

class Query(ObjectType):
    all_inventory = List(ItemType)
    all_orders = List(OrderType)
    order = Field(OrderType, id=Int())
    all_logistic_requests = List(LogisticRequestType)
    logistic_request = Field(LogisticRequestType, itemCode=String())  # Change to itemCode

    def resolve_all_inventory(self, info):
        inventory_service_url = 'http://localhost:5003/graphql'
        query = '''
        query {
            allInventory {
                itemCode
                name
                description
                unit
                minStor
                location
            }
        }
        '''
        try:
            response = requests.post(inventory_service_url, json={'query': query})
            response.raise_for_status()
            return response.json()['data']['allInventory']
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data from Inventory Service: {e}")
            return []

    def resolve_all_orders(self, info):
        logistic_service_url = 'http://localhost:5002/graphql'
        query = '''
        query {
          allOrders {
            orderId
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
            orders = response.json()['data']['allOrders']

            inventory_service_url = 'http://localhost:5003/graphql'
            for order in orders:
                item_id = order['itemId']
                item_query = f'''
                query {{
                  inventoryItem(id: {item_id}) {{
                    itemCode
                    name
                    description
                    unit
                    minStor
                    location
                  }}
                }}
                '''
                item_response = requests.post(inventory_service_url, json={'query': item_query})
                item_response.raise_for_status()
                item_data = item_response.json()['data']['inventoryItem']
                order['item'] = item_data

            return orders
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orders: {e}")
            return []

    def resolve_order(self, info, id):
        return Order.query.get(id)

    def resolve_logisticRequest(self, info, itemCode):
        inventory_service_url = 'http://localhost:5003/graphql'
        
        query = f'''
        query {{
            inventoryItem(itemCode: "{itemCode}") {{
                id
                itemCode
                name
                quantity
                description
                unit
                minStor
                location
            }}
        }}
        '''
        
        try:
            response = requests.post(inventory_service_url, json={'query': query})
            response.raise_for_status()  # Check for errors in the request
            
            # Periksa jika response.json() tidak error
            data = response.json()
            
            # Pastikan ada data inventoryItem
            item_data = data.get('data', {}).get('inventoryItem', None)
            
            if not item_data:
                raise Exception(f"Item with itemCode {itemCode} not found in inventory service")
            
            # Mengambil data yang diperlukan untuk permintaan logistik
            logistic_request = LogisticRequest(
                item_id=item_data['id'],
                quantity=10,  # Placeholder, bisa diganti dengan data input
                reference="Ref001",  # Placeholder, bisa diganti dengan data input
                created_by=1,  # Placeholder, bisa diganti dengan data input
                created_at=datetime.utcnow(),
                status="pending"
            )
            
            # Menyimpan data permintaan logistik
            db.session.add(logistic_request)
            db.session.commit()

            return logistic_request

        except requests.exceptions.RequestException as e:
            print(f"Error fetching item from Inventory Service: {e}")
            raise Exception(f"Error fetching item from Inventory Service: {e}")
        except Exception as e:
            print(f"Error creating logistic request: {e}")
            raise Exception(f"Error creating logistic request: {e}")


    def resolve_all_logistic_requests(self, info):
        logistic_service_url = 'http://localhost:5002/graphql'
        query = '''
        query {
          allLogisticRequests {
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
            logistic_requests = response.json()['data']['allLogisticRequests']

            for logistic_request in logistic_requests:
                item_id = logistic_request['itemId']
                item_query = f'''
                query {{
                  inventoryItem(id: {item_id}) {{
                    itemCode
                    name
                    description
                    unit
                    minStor
                    location
                  }}
                }}
                '''
                item_response = requests.post(logistic_service_url, json={'query': item_query})
                item_response.raise_for_status()
                item_data = item_response.json()['data']['inventoryItem']
                logistic_request['item'] = item_data

            return logistic_requests

        except requests.exceptions.RequestException as e:
            print(f"Error fetching logistic requests: {e}")
            return []

# CreateLogisticRequest Mutation
class CreateLogisticRequest(Mutation):
    class Arguments:
        itemCode = String(required=True)
        quantity = Int(required=True)
        reference = String()
        createdBy = Int(required=True)

    logisticRequest = Field(LogisticRequestType)

    def mutate(self, info, itemCode, quantity, reference, createdBy):
        # URL untuk mengambil data dari inventory service
        inventory_service_url = 'http://localhost:5003/graphql'  # Ganti dengan URL `inventory-service`

        query = f'''
        query {{
            inventoryItem(itemCode: "{itemCode}") {{
                id
                itemCode
                name
                quantity
                description
                unit
                minStor
                location
            }}
        }}
        '''

        try:
            # Mengambil data item dari inventory-service
            response = requests.post(inventory_service_url, json={'query': query})
            response.raise_for_status()  # Memastikan tidak ada error
            item_data = response.json()['data']['inventoryItem']

            # Periksa apakah item ditemukan, jika tidak, beri pesan error
            if not item_data:
                raise Exception(f"Item with itemCode {itemCode} not found in inventory service")

            # Pastikan itemId tersedia dan valid sebelum membuat permintaan logistik
            item_id = item_data.get('id')
            if not item_id:
                raise Exception(f"Item ID for {itemCode} is missing or invalid")

            # Buat permintaan logistik hanya jika item ditemukan di inventory
            logistic_request = LogisticRequest(
                item_id=item_id,  # Gunakan item_id yang valid dari inventory
                quantity=quantity,
                reference=reference,
                created_by=createdBy,
                created_at=datetime.utcnow(),  # Pastikan created_at terisi
                status="pending"  # Status awal adalah "pending"
            )

            # Menambahkan permintaan logistik ke database
            db.session.add(logistic_request)
            db.session.commit()

            # Mengembalikan data permintaan logistik yang baru dibuat
            return CreateLogisticRequest(logisticRequest=logistic_request)

        except requests.exceptions.RequestException as e:
            # Tangani error dari request inventory-service
            raise Exception(f"Failed to fetch item from Inventory Service: {e}")
        except Exception as e:
            # Tangani error lain
            raise Exception(f"Error creating logistic request: {e}")

class Mutation(ObjectType):
    create_logistic_request = CreateLogisticRequest.Field()

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

@app.route('/logistic')
def serve_logistic_index():
    return send_from_directory('frontend/logistic', 'index.html')

@app.route('/logistic/<path:path>')
def serve_logistic_static(path):
    return send_from_directory('frontend/logistic', path)

with app.app_context():
    db.create_all()

@app.route('/logistic/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')

    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    order = Order(
        item_id=item_id,
        quantity=quantity,
        reference=reference,
        created_at=datetime.utcnow(),
        status="pending"
    )
    
    try:
        db.session.add(order)
        db.session.commit()
        return jsonify({'message': 'Order created successfully', 'order_id': order.order_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error creating order'}), 500

@app.route('/logistic/view-items', methods=['GET'])
def view_items():
    inventory_service_url = 'http://localhost:5003/graphql'

    query = '''
    query {
        allInventory {
            itemCode
            name
            description
            unit
            minStor
            location
        }
    }
    '''

    try:
        response = requests.post(inventory_service_url, json={'query': query})
        response.raise_for_status()
        items = response.json()['data']['allInventory']
        return jsonify(items)
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Failed to get items: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
