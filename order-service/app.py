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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///order_service.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

db = SQLAlchemy(app)
CORS(app)

# Inventory Service URL (untuk komunikasi antar service)
INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001')

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

# GraphQL Schema
class OrderType(SQLAlchemyObjectType):
    class Meta:
        model = Order
        load_instance = True

class OrderItemType(SQLAlchemyObjectType):
    class Meta:
        model = OrderItem
        load_instance = True

class Query(graphene.ObjectType):
    orders = graphene.List(OrderType, 
                          restaurant_id=graphene.String(),
                          status=graphene.String())
    order = graphene.Field(OrderType, id=graphene.Int())
    order_by_number = graphene.Field(OrderType, order_number=graphene.String())
    order_items = graphene.List(OrderItemType)
    
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
    def resolve_order_items(self, info):
        return OrderItem.query.all()

class CreateOrder(graphene.Mutation):
    class Arguments:
        restaurant_id = graphene.String(required=True)
        restaurant_name = graphene.String(required=True)
        requested_date = graphene.String(required=True)
        notes = graphene.String()
        items = graphene.List(graphene.String, required=True)  # JSON string of items
    
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, restaurant_id, restaurant_name, requested_date, items, notes=None):
        try:
            # Generate order number
            order_count = Order.query.count() + 1
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{order_count:04d}"
            
            # Parse requested date
            req_date = datetime.strptime(requested_date, '%Y-%m-%d %H:%M:%S')
            
            # Create order
            order = Order(
                order_number=order_number,
                restaurant_id=restaurant_id,
                restaurant_name=restaurant_name,
                requested_date=req_date,
                notes=notes,
                status=OrderStatus.PENDING
            )
            
            db.session.add(order)
            db.session.flush()  # Get order ID
            
            # Add order items
            import json
            total_items = 0
            for item_data in items:
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
            
            order.total_items = total_items
            db.session.commit()
            
            return CreateOrder(order=order, success=True, message="Order created successfully")
            
        except Exception as e:
            db.session.rollback()
            return CreateOrder(order=None, success=False, message=str(e))

class UpdateOrderStatus(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int(required=True)
        status = graphene.String(required=True)
        approved_quantities = graphene.List(graphene.String)  # JSON string of item quantities
    
    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, order_id, status, approved_quantities=None):
        try:
            order = Order.query.get(order_id)
            if not order:
                return UpdateOrderStatus(order=None, success=False, message="Order not found")
            
            # Update status
            try:
                new_status = OrderStatus(status.upper())
                order.status = new_status
            except ValueError:
                return UpdateOrderStatus(order=None, success=False, message="Invalid status")
            
            # Update timestamps based on status
            now = datetime.utcnow()
            if new_status == OrderStatus.APPROVED:
                order.approved_date = now
                
                # Update approved quantities if provided
                if approved_quantities:
                    import json
                    for qty_data in approved_quantities:
                        qty = json.loads(qty_data)
                        item = OrderItem.query.filter_by(
                            order_id=order_id,
                            item_code=qty['item_code']
                        ).first()
                        if item:
                            item.approved_quantity = qty['approved_quantity']
                            
            elif new_status == OrderStatus.SHIPPED:
                order.shipped_date = now
            elif new_status == OrderStatus.DELIVERED:
                order.delivered_date = now
            
            order.updated_at = now
            db.session.commit()
            
            return UpdateOrderStatus(order=order, success=True, message="Order status updated successfully")
            
        except Exception as e:
            db.session.rollback()
            return UpdateOrderStatus(order=None, success=False, message=str(e))

class CheckInventoryAvailability(graphene.Mutation):
    class Arguments:
        items = graphene.List(graphene.String, required=True)  # JSON items to check
    
    available = graphene.Boolean()
    message = graphene.String()
    availability_details = graphene.List(graphene.String)
    
    def mutate(self, info, items):
        try:
            # Call Inventory Service to check availability
            import json
            check_items = []
            for item_data in items:
                item = json.loads(item_data)
                check_items.append({
                    'item_code': item['item_code'],
                    'requested_quantity': item['requested_quantity']
                })
            
            # Mock API call to inventory service
            # In real implementation, replace with actual HTTP request
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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'order-service'})

# CORS headers untuk frontend
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5002, debug=True)