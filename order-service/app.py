import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_graphql import GraphQLView
from flask_cors import CORS
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from datetime import datetime
import requests
import os
from enum import Enum
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///order_service.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
db = SQLAlchemy(app)
CORS(app)

# Inventory Service URL (untuk komunikasi antar service)
INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://localhost:5000')

# Models
class OrderStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED" 
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    restaurant_id = db.Column(db.String(100), nullable=False)
    restaurant_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_items = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    requested_date = db.Column(db.DateTime, nullable=False)
    approved_date = db.Column(db.DateTime)
    shipped_date = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    requested_quantity = db.Column(db.Integer, nullable=False)
    approved_quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def get_inventory_items():
    """Helper function untuk mengambil list item dari inventory service"""
    try:
        response = requests.get(f"{INVENTORY_SERVICE_URL}/api/items", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.RequestException:
        return []

def check_inventory_availability_helper(items):
    """Helper function untuk mengecek ketersediaan inventory"""
    try:
        check_items = []
        for item in items:
            if isinstance(item, str):
                item_data = json.loads(item)
            else:
                item_data = item
                
            check_items.append({
                'item_code': item_data['item_code'],
                'requested_quantity': item_data['requested_quantity']
            })
        
        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/api/check-availability",
            json={'items': check_items},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                'available': False,
                'message': 'Failed to check inventory availability',
                'details': []
            }
            
    except requests.RequestException as e:
        # Fallback ketika inventory service tidak tersedia
        return {
            'available': True,  # Asumsikan tersedia untuk development
            'message': f"Inventory service unavailable: {str(e)}",
            'details': []
        }

def get_inventory_stock(item_code):
    """Helper function untuk mengambil stok item dari inventory service"""
    try:
        response = requests.get(f"{INVENTORY_SERVICE_URL}/api/items/{item_code}/stock", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {'stock_quantity': 0}
    except requests.RequestException:
        return {'stock_quantity': 0}

def reserve_inventory_stock(order_id, items):
    """Helper function untuk reserve stock di inventory"""
    try:
        reserve_items = []
        for item in items:
            reserve_items.append({
                'item_code': item.item_code,
                'quantity': item.approved_quantity if item.approved_quantity > 0 else item.requested_quantity
            })
        
        response = requests.post(
            f"{INVENTORY_SERVICE_URL}/api/reserve-stock",
            json={
                'order_id': order_id,
                'items': reserve_items
            },
            timeout=10
        )
        
        return response.status_code == 200, response.json() if response.status_code == 200 else {}
        
    except requests.RequestException:
        return False, {'message': 'Failed to reserve stock'}

# GraphQL Schema
class OrderType(SQLAlchemyObjectType):
    class Meta:
        model = Order
        load_instance = True

class OrderItemType(SQLAlchemyObjectType):
    class Meta:
        model = OrderItem
        load_instance = True

class InventoryItemType(graphene.ObjectType):
    """Type untuk item dari inventory service"""
    id = graphene.Int()
    item_code = graphene.String()
    name = graphene.String()
    description = graphene.String()
    category = graphene.String()
    unit = graphene.String()
    unit_price = graphene.Float()
    stock_quantity = graphene.Int()

class Query(graphene.ObjectType):
    orders = graphene.List(OrderType, 
                          restaurant_id=graphene.String(),
                          status=graphene.String())
    order = graphene.Field(OrderType, id=graphene.Int())
    order_by_number = graphene.Field(OrderType, order_number=graphene.String())
    
    # New queries for inventory integration
    inventory_items = graphene.List(InventoryItemType)
    inventory_item_stock = graphene.Field(graphene.Int, item_code=graphene.String(required=True))
    approved_orders = graphene.List(OrderType)  # Untuk dropdown di inventory service
    
    def resolve_orders(self, info, restaurant_id=None, status=None):
        query = Order.query
        
        if restaurant_id:
            query = query.filter(Order.restaurant_id == restaurant_id)
        
        if status:
            try:
                status_enum = OrderStatus(status.upper())
                query = query.filter(Order.status == status_enum)
            except ValueError:
                return []
        
        return query.order_by(Order.created_at.desc()).all()
    
    def resolve_order(self, info, id):
        return Order.query.get(id)
    
    def resolve_order_by_number(self, info, order_number):
        return Order.query.filter(Order.order_number == order_number).first()
    
    def resolve_inventory_items(self, info):
        """Mengambil list item dari inventory service"""
        items_data = get_inventory_items()
        inventory_items = []
        for item_data in items_data:
            inventory_items.append(InventoryItemType(
                id=item_data.get('id'),
                item_code=item_data.get('item_code'),
                name=item_data.get('name'),
                description=item_data.get('description'),
                category=item_data.get('category'),
                unit=item_data.get('unit'),
                unit_price=item_data.get('unit_price'),
                stock_quantity=item_data.get('stock_quantity')
            ))
        return inventory_items
    
    def resolve_inventory_item_stock(self, info, item_code):
        """Mengambil stok item dari inventory service"""
        stock_data = get_inventory_stock(item_code)
        return stock_data.get('stock_quantity', 0)
    
    def resolve_approved_orders(self, info):
        """Mengambil orders yang sudah approved untuk dropdown di inventory service"""
        return Order.query.filter(Order.status == OrderStatus.APPROVED).order_by(Order.approved_date.desc()).all()

class CreateOrder(graphene.Mutation):
    class Arguments:
        restaurant_id = graphene.String(required=True)
        restaurant_name = graphene.String(required=True)
        requested_date = graphene.String(required=True)
        notes = graphene.String()
        items = graphene.List(graphene.String, required=True)
        check_inventory = graphene.Boolean(default_value=True)  # Option untuk cek inventory
    
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    inventory_check = graphene.String()  # Detail hasil cek inventory
    
    def mutate(self, info, restaurant_id, restaurant_name, requested_date, items, notes=None, check_inventory=True):
        try:
            # Cek inventory availability terlebih dahulu jika diminta
            inventory_result = None
            if check_inventory:
                inventory_result = check_inventory_availability_helper(items)
                
                if not inventory_result['available']:
                    return CreateOrder(
                        order=None, 
                        success=False, 
                        message="Some items are not available in sufficient quantity",
                        inventory_check=json.dumps(inventory_result)
                    )
            
            # Generate order number
            order_count = Order.query.count() + 1
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_count:04d}"
            
            # Parse requested date - handle both formats
            try:
                if 'T' in requested_date:
                    req_date = datetime.fromisoformat(requested_date.replace('Z', ''))
                else:
                    req_date = datetime.strptime(requested_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try alternative format
                req_date = datetime.fromisoformat(requested_date.replace('T', ' ').replace('Z', ''))
            
            # Create order
            order = Order(
                order_number=order_number,
                restaurant_id=restaurant_id,
                restaurant_name=restaurant_name,
                requested_date=req_date,
                notes=notes or '',
                status=OrderStatus.PENDING
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Add order items
            total_items = 0
            for item_data in items:
                try:
                    item = json.loads(item_data)
                    order_item = OrderItem(
                        order_id=order.id,
                        item_code=item['item_code'],
                        item_name=item['item_name'],
                        requested_quantity=item['requested_quantity'],
                        unit=item['unit'],
                        notes=item.get('notes', '')
                    )
                    db.session.add(order_item)
                    total_items += item['requested_quantity']
                except (json.JSONDecodeError, KeyError) as e:
                    db.session.rollback()
                    return CreateOrder(
                        order=None, 
                        success=False, 
                        message=f"Invalid item data: {str(e)}",
                        inventory_check=None
                    )
            
            order.total_items = total_items
            db.session.commit()
            
            return CreateOrder(
                order=order, 
                success=True, 
                message="Order created successfully",
                inventory_check=json.dumps(inventory_result) if inventory_result else None
            )
            
        except Exception as e:
            db.session.rollback()
            return CreateOrder(
                order=None, 
                success=False, 
                message=str(e),
                inventory_check=None
            )

class UpdateOrderStatus(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int(required=True)
        status = graphene.String(required=True)
        approved_quantities = graphene.List(graphene.String)  # JSON string of item quantities
        reserve_stock = graphene.Boolean(default_value=True)  # Option untuk reserve stock
    
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    stock_reservation = graphene.String()  # Detail reservasi stock
    
    def mutate(self, info, order_id, status, approved_quantities=None, reserve_stock=True):
        try:
            order = Order.query.get(order_id)
            if not order:
                return UpdateOrderStatus(
                    order=None, 
                    success=False, 
                    message="Order not found",
                    stock_reservation=None
                )
            
            # Update status
            try:
                new_status = OrderStatus(status.upper())
                order.status = new_status
            except ValueError:
                return UpdateOrderStatus(
                    order=None, 
                    success=False, 
                    message="Invalid status",
                    stock_reservation=None
                )
            
            # Update timestamps dan handle approved quantities
            now = datetime.utcnow()
            stock_reservation_result = None
            
            if new_status == OrderStatus.APPROVED:
                order.approved_date = now
                
                # Update approved quantities if provided
                if approved_quantities:
                    for qty_data in approved_quantities:
                        qty = json.loads(qty_data)
                        item = OrderItem.query.filter_by(
                            order_id=order_id,
                            item_code=qty['item_code']
                        ).first()
                        if item:
                            item.approved_quantity = qty['approved_quantity']
                
                # Reserve stock di inventory service
                if reserve_stock:
                    success, reservation_result = reserve_inventory_stock(order_id, order.items)
                    stock_reservation_result = reservation_result
                    
                    if not success:
                        db.session.rollback()
                        return UpdateOrderStatus(
                            order=None,
                            success=False,
                            message=f"Failed to reserve stock: {reservation_result.get('message', 'Unknown error')}",
                            stock_reservation=json.dumps(reservation_result)
                        )
                        
            elif new_status == OrderStatus.SHIPPED:
                order.shipped_date = now
            elif new_status == OrderStatus.DELIVERED:
                order.delivered_date = now
            
            order.updated_at = now
            db.session.commit()
            
            return UpdateOrderStatus(
                order=order, 
                success=True, 
                message="Order status updated successfully",
                stock_reservation=json.dumps(stock_reservation_result) if stock_reservation_result else None
            )
            
        except Exception as e:
            db.session.rollback()
            return UpdateOrderStatus(
                order=None, 
                success=False, 
                message=str(e),
                stock_reservation=None
            )

class CheckInventoryAvailability(graphene.Mutation):
    class Arguments:
        items = graphene.List(graphene.String, required=True)  # JSON items to check
    
    available = graphene.Boolean()
    message = graphene.String()
    availability_details = graphene.List(graphene.String)
    
    def mutate(self, info, items):
        try:
            # Call Inventory Service to check availability
            check_items = []
            for item_data in items:
                item = json.loads(item_data)
                check_items.append({
                    'item_code': item['item_code'],
                    'requested_quantity': item['requested_quantity']
                })
            
            # Mock API call to inventory service
            try:
                response = requests.post(
                    f"{INVENTORY_SERVICE_URL}/api/check-availability",
                    json={'items': check_items},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return CheckInventoryAvailability(
                        available=result.get('available', False),
                        message=result.get('message', ''),
                        availability_details=[json.dumps(detail) for detail in result.get('details', [])]
                    )
                else:
                    return CheckInventoryAvailability(
                        available=False,
                        message="Failed to check inventory availability",
                        availability_details=[]
                    )
            except requests.RequestException:
                # Fallback when inventory service is not available
                return CheckInventoryAvailability(
                    available=True,  # Assume available for development
                    message="Inventory service unavailable, assuming items are available",
                    availability_details=[]
                )
                
        except Exception as e:
            return CheckInventoryAvailability(
                available=False,
                message=str(e),
                availability_details=[]
            )

class Mutation(graphene.ObjectType):
    create_order = CreateOrder.Field()
    update_order_status = UpdateOrderStatus.Field()
    check_inventory_availability = CheckInventoryAvailability.Field()

# Create GraphQL schema
schema = graphene.Schema(query=Query, mutation=Mutation)

# Add GraphQL endpoint
app.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True)
)

# REST API endpoints for external service integration
@app.route('/api/orders', methods=['POST'])
def create_order_rest():
    """REST endpoint for creating orders from restaurant system"""
    try:
        data = request.get_json()
        
        # Generate order number
        order_count = Order.query.count() + 1
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_count:04d}"
        
        # Create order
        order = Order(
            order_number=order_number,
            restaurant_id=data['restaurant_id'],
            restaurant_name=data['restaurant_name'],
            requested_date=datetime.strptime(data['requested_date'], '%Y-%m-%d %H:%M:%S'),
            notes=data.get('notes', ''),
            status=OrderStatus.PENDING
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Add items
        total_items = 0
        for item_data in data['items']:
            order_item = OrderItem(
                order_id=order.id,
                item_code=item_data['item_code'],
                item_name=item_data['item_name'],
                requested_quantity=item_data['requested_quantity'],
                unit=item_data['unit'],
                notes=item_data.get('notes', '')
            )
            db.session.add(order_item)
            total_items += item_data['requested_quantity']
        
        order.total_items = total_items
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'order_id': order.id,
            'message': 'Order created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/orders/<order_number>/status', methods=['GET'])
def get_order_status(order_number):
    """REST endpoint for checking order status"""
    order = Order.query.filter_by(order_number=order_number).first()
    
    if not order:
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'status': order.status.value,
        'restaurant_id': order.restaurant_id,
        'restaurant_name': order.restaurant_name,
        'created_at': order.created_at.isoformat(),
        'updated_at': order.updated_at.isoformat(),
        'items': [{
            'item_code': item.item_code,
            'item_name': item.item_name,
            'requested_quantity': item.requested_quantity,
            'approved_quantity': item.approved_quantity,
            'unit': item.unit
        } for item in order.items]
    })

@app.route('/api/orders/approved', methods=['GET'])
def get_approved_orders():
    """REST endpoint untuk mengambil orders yang sudah approved (untuk inventory service)"""
    approved_orders = Order.query.filter(Order.status == OrderStatus.APPROVED).order_by(Order.approved_date.desc()).all()
    
    orders_data = []
    for order in approved_orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'restaurant_name': order.restaurant_name,
            'approved_date': order.approved_date.isoformat() if order.approved_date else None,
            'items': [{
                'item_code': item.item_code,
                'item_name': item.item_name,
                'approved_quantity': item.approved_quantity
            } for item in order.items]
        })
    
    return jsonify(orders_data)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'order-service'})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)