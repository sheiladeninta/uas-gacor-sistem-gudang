import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Schema, Int, Field, List, Mutation
from datetime import datetime
import requests
import os
from models import db, Item, Order, LogisticRequest  # Pastikan model LogisticRequest sudah ada

# Initialize the Flask app
app = Flask(__name__)
CORS(app)

# Database Configuration
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'logistic-management.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # Absolute path to the DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking
db.init_app(app)

# GraphQL Schema for Logistic Service
class ItemType(ObjectType):
    itemId = Int()  # Use itemId instead of item_id
    itemCode = String()  # Use itemCode instead of item_code
    name = String()
    description = String()
    unit = String()
    minStor = Int()  # Use minStor instead of min_stor
    location = String()

class OrderType(ObjectType):
    orderId = Int()  # Use orderId instead of order_id
    itemId = Int()  # Use itemId instead of item_id
    quantity = Int()
    reference = String()
    status = String()
    createdAt = String()  # Use createdAt instead of created_at

# Query for fetching all items and orders
class Query(ObjectType):
    all_items = List(ItemType)
    all_orders = List(OrderType)
    order = Field(OrderType, id=Int())

    def resolve_all_items(self, info):
        return Item.query.all()  # Fetch all items

    def resolve_all_orders(self, info):
        return Order.query.all()  # Fetch all orders
    
    def resolve_order(self, info, id):
        return Order.query.get(id)  # Fetch order by orderId (id)

# Mutation for creating orders and calling the Inventory Service for inbound transactions
class CreateOrder(Mutation):
    class Arguments:
        item_id = Int(required=True)
        quantity = Int(required=True)
        reference = String()

    order = Field(OrderType)

    def mutate(self, info, item_id, quantity, reference):
        # Fetch the item from the database
        item = Item.query.get(item_id)
        if not item:
            raise Exception("Item not found")
        
        # Create the order
        order = Order(
            item_id=item_id,
            quantity=quantity,
            reference=reference,
            created_at=datetime.utcnow(),  # Ensure datetime is used correctly
            status="pending"
        )
        db.session.add(order)
        db.session.commit()

        # Call Inventory Service to create the inventory log for inbound
        self.create_inventory_inbound_log(item_id, quantity, reference)

        return CreateOrder(order=order)

    def create_inventory_inbound_log(self, item_id, quantity, reference):
        # Integrasi dengan Inventory Service
        inventory_service_url = 'http://localhost:5003/graphql'  # URL dari Inventory Service

        mutation = '''
        mutation {
            createInventoryLog(
                itemId: %d,
                logType: "inbound",
                quantity: %d,
                reference: "%s",
                createdBy: 1
            ) {
                inventoryLog {
                    id
                    itemId
                    logType
                    quantity
                    reference
                    createdAt
                }
            }
        }
        ''' % (item_id, quantity, reference)

        try:
            # Mengirimkan permintaan ke Inventory Service
            response = requests.post(inventory_service_url, json={'query': mutation})
            response.raise_for_status()  # Jika permintaan gagal, akan raise exception
            print("Inventory inbound log created successfully")
        except Exception as e:
            print(f"Error creating inventory log: {e}")


# Mutation to create an order
class Mutation(ObjectType):
    create_order = CreateOrder.Field()

# Create GraphQL Schema
schema = Schema(query=Query, mutation=Mutation)

# Add GraphQL endpoint to the Flask app
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True  # Enable GraphiQL interface
    )
)

# Flask route to serve static files
@app.route('/logistic')
def serve_logistic_index():
    return send_from_directory('frontend/logistic', 'index.html')

@app.route('/logistic/<path:path>')
def serve_logistic_static(path):
    return send_from_directory('frontend/logistic', path)

# Initialize the database schema
with app.app_context():
    db.create_all()  # Create tables for the models if they do not exist

@app.route('/logistic/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    
    # Mengambil data dari body request
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    reference = data.get('reference')

    # Cek apakah item ada di database
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    # Membuat order baru
    order = Order(
        item_id=item_id,
        quantity=quantity,
        reference=reference,
        created_at=datetime.utcnow(),
        status="pending"
    )
    
    try:
        db.session.add(order)
        db.session.commit()  # Menyimpan ke database
        print(f"Order Created: {order.order_id}")  # Log di server

        # Mengintegrasi dengan Inventory Service untuk membuat log inbound
        create_inventory_inbound_log(item_id, quantity, reference)

        return jsonify({'message': 'Order created successfully', 'order_id': order.order_id}), 201

    except Exception as e:
        db.session.rollback()  # Rollback jika terjadi error
        print(f"Error creating order: {e}")
        return jsonify({'error': 'Error creating order'}), 500


@app.route('/logistic/view-orders', methods=['GET'])
def view_orders():
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders])  # Pastikan ada to_dict() atau serialize function di model Order

@app.route('/api/logistic/requests', methods=['GET'])
def get_logistic_requests():
    requests = LogisticRequest.query.all()
    return jsonify([req.serialize() for req in requests])

@app.route('/api/logistic/request', methods=['POST'])
def create_logistic_request():
    data = request.get_json()

    # Membuat permintaan baru
    new_request = LogisticRequest(
        item_id=data['item_id'],
        quantity=data['quantity'],
        reference=data['reference'],
        created_by=data['created_by'],
    )

    db.session.add(new_request)
    db.session.commit()

    # Kirim permintaan ke Inventory Service
    response = requests.post('http://inventory-service-url/api/inventory/logs', json={
        'item_id': data['item_id'],
        'log_type': 'request',
        'quantity': data['quantity'],
        'reference': data['reference'],
        'created_by': data['created_by'],
        'status': 'pending'
    })

    if response.status_code == 201:
        return jsonify({"message": "Request created and sent to Inventory Service"}), 201
    else:
        db.session.rollback()
        return jsonify({"error": "Failed to send request to Inventory Service"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)  # Run the application on port 5002
