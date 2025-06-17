import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime
from decimal import Decimal
import json
import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene import ObjectType
from flask_graphql import GraphQLView
# from config import Config
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Tentukan folder instance dan pastikan file db berada di dalamnya
db_path = os.path.join(app.instance_path, 'inventory-service.db')
# Gunakan os.path.abspath() untuk mendapatkan path absolut yang valid
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.abspath(db_path)}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi db
db = SQLAlchemy(app)

# Pastikan folder instance ada
if not os.path.exists(app.instance_path):
    os.makedirs(app.instance_path)

# Order Service URL (untuk komunikasi antar service)
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:5002')

# Model Item
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False, default="pcs")
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    stock_quantity = db.Column(db.Integer, default=0)
    reserved_quantity = db.Column(db.Integer, default=0)  # Tambahan untuk stock yang direserve
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f'<Item {self.item_code}: {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'item_code': self.item_code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit': self.unit,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'stock_quantity': self.stock_quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.stock_quantity - self.reserved_quantity,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def update_stock(self, quantity):
        self.stock_quantity += quantity

    @property
    def available_quantity(self):
        return self.stock_quantity - self.reserved_quantity

class QCLog(db.Model):
    __tablename__ = 'qc_logs'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)  
    order_number = db.Column(db.String(50), nullable=False)  # Tambahan order number untuk referensi
    restaurant_name = db.Column(db.String(200), nullable=False)  # Tambahan nama restaurant
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sent_to_qc_at = db.Column(db.DateTime, default=datetime.utcnow)
    qc_status = db.Column(db.String(20), default="PENDING")  # PENDING, PASSED, FAILED
    qc_notes = db.Column(db.Text)  # Catatan QC
    processed_by = db.Column(db.String(100))  # Staff yang memproses

    def __repr__(self):
        return f"<QCLog Order #{self.order_number}: {self.item_code}, Qty: {self.quantity}>"

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'order_number': self.order_number,
            'restaurant_name': self.restaurant_name,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'sent_to_qc_at': self.sent_to_qc_at.isoformat(),
            'qc_status': self.qc_status,
            'qc_notes': self.qc_notes,
            'processed_by': self.processed_by
        }

# Helper Functions untuk komunikasi dengan Order Service
def get_approved_orders():
    """Helper function untuk mengambil approved orders dari order service"""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/api/orders/approved", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except requests.RequestException:
        return []

# GraphQL schema untuk Item
class ItemType(SQLAlchemyObjectType):
    class Meta:
        model = Item
        fields = ('id', 'item_code', 'name', 'description', 'category', 'unit', 'unit_price', 'stock_quantity', 'reserved_quantity', 'created_at', 'updated_at')
    
    available_quantity = graphene.Int()
    
    def resolve_available_quantity(self, info):
        return self.available_quantity

class QCLogType(SQLAlchemyObjectType):
    class Meta:
        model = QCLog
        fields = ('id', 'order_id', 'order_number', 'restaurant_name', 'item_code', 'item_name', 'quantity', 'sent_to_qc_at', 'qc_status', 'qc_notes', 'processed_by')

# Type untuk approved orders dari order service
class ApprovedOrderType(graphene.ObjectType):
    id = graphene.Int()
    order_number = graphene.String()
    restaurant_name = graphene.String()
    approved_date = graphene.String()
    items = graphene.List(graphene.String)  # JSON string untuk items

# Query untuk mendapatkan semua item dan QC logs
class Query(graphene.ObjectType):
    items = graphene.List(ItemType)
    item_by_code = graphene.Field(ItemType, item_code=graphene.String(required=True))
    qc_logs = graphene.List(QCLogType, status=graphene.String())
    approved_orders = graphene.List(ApprovedOrderType)  # Orders yang bisa dikirim ke QC
    low_stock_items = graphene.List(ItemType, threshold=graphene.Int(default_value=10))
    
    def resolve_items(self, info):
        return Item.query.all()
    
    def resolve_item_by_code(self, info, item_code):
        return Item.query.filter_by(item_code=item_code).first()
    
    def resolve_qc_logs(self, info, status=None):
        query = QCLog.query
        if status:
            query = query.filter(QCLog.qc_status == status.upper())
        return query.order_by(QCLog.sent_to_qc_at.desc()).all()
    
    def resolve_approved_orders(self, info):
        """Mengambil approved orders dari order service yang belum dikirim ke QC"""
        orders_data = get_approved_orders()
        approved_orders = []
        
        for order_data in orders_data:
            # Cek apakah order sudah pernah dikirim ke QC
            existing_qc = QCLog.query.filter_by(order_id=order_data['id']).first()
            if not existing_qc:  # Hanya tampilkan yang belum dikirim ke QC
                approved_orders.append(ApprovedOrderType(
                    id=order_data['id'],
                    order_number=order_data['order_number'],
                    restaurant_name=order_data['restaurant_name'],
                    approved_date=order_data.get('approved_date'),
                    items=[json.dumps(item) for item in order_data['items']]
                ))
        
        return approved_orders
    
    def resolve_low_stock_items(self, info, threshold):
        """Mengambil items dengan stock rendah"""
        return Item.query.filter(Item.stock_quantity <= threshold).all()

# Mutations
class CreateItem(graphene.Mutation):
    class Arguments:
        item_code = graphene.String(required=True)
        name = graphene.String(required=True)
        stock_quantity = graphene.Int(required=True)
        description = graphene.String()
        unit = graphene.String()
        category = graphene.String()
        unit_price = graphene.Float()

    item = graphene.Field(ItemType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_code, name, stock_quantity, description=None, unit="pcs", category="Uncategorized", unit_price=0.0):
        existing_item = Item.query.filter_by(item_code=item_code).first()
        if existing_item:
            return CreateItem(success=False, message=f"Item with code '{item_code}' already exists.")

        new_item = Item(
            item_code=item_code,
            name=name,
            stock_quantity=stock_quantity,
            description=description,
            unit=unit,
            category=category,
            unit_price=unit_price
        )
        
        db.session.add(new_item)
        db.session.commit()
        
        return CreateItem(item=new_item, success=True, message="Item created successfully.")

class UpdateItem(graphene.Mutation):
    class Arguments:
        item_code = graphene.String(required=True)
        name = graphene.String()
        stock_quantity = graphene.Int()
        description = graphene.String()
        unit = graphene.String()
        category = graphene.String()
        unit_price = graphene.Float()

    item = graphene.Field(ItemType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_code, name=None, stock_quantity=None, description=None, unit=None, category=None, unit_price=None):
        item = Item.query.filter_by(item_code=item_code).first()
        if not item:
            return UpdateItem(success=False, message=f"Item with code '{item_code}' not found.")

        if name is not None:
            item.name = name
        if stock_quantity is not None:
            item.stock_quantity = stock_quantity
        if description is not None:
            item.description = description
        if unit is not None:
            item.unit = unit
        if category is not None:
            item.category = category
        if unit_price is not None:
            item.unit_price = unit_price

        db.session.commit()
        return UpdateItem(item=item, success=True, message="Item updated successfully.")

class DeleteItem(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, id):
        item = Item.query.get(id)
        if not item:
            return DeleteItem(success=False, message=f"Item with id '{id}' not found.")

        db.session.delete(item)
        db.session.commit()
        return DeleteItem(success=True, message="Item deleted successfully.")

class SendToQC(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    qc_logs = graphene.List(QCLogType)

    def mutate(self, info, order_id):
        try:
            # Ambil data order dari order service
            orders_data = get_approved_orders()
            selected_order = None
            
            for order_data in orders_data:
                if order_data['id'] == order_id:
                    selected_order = order_data
                    break
            
            if not selected_order:
                return SendToQC(success=False, message="Order not found or not approved.")
            
            # Cek apakah order sudah pernah dikirim ke QC
            existing_qc = QCLog.query.filter_by(order_id=order_id).first()
            if existing_qc:
                return SendToQC(success=False, message="Order already sent to QC.")
            
            qc_logs_created = []
            
            # Proses setiap item dalam order
            for item_data in selected_order['items']:
                item_code = item_data['item_code']
                item_name = item_data['item_name']
                quantity = item_data['approved_quantity']
                
                # Cek ketersediaan stock
                item = Item.query.filter_by(item_code=item_code).first()
                if not item:
                    return SendToQC(success=False, message=f"Item {item_code} not found in inventory.")
                
                if item.available_quantity < quantity:
                    return SendToQC(success=False, message=f"Insufficient stock for item {item_code}. Available: {item.available_quantity}, Required: {quantity}")
                
                # Kurangi stock dan tambah reserved
                item.stock_quantity -= quantity
                
                # Buat QC Log
                qc_log = QCLog(
                    order_id=order_id,
                    order_number=selected_order['order_number'],
                    restaurant_name=selected_order['restaurant_name'],
                    item_code=item_code,
                    item_name=item_name,
                    quantity=quantity
                )
                
                db.session.add(qc_log)
                qc_logs_created.append(qc_log)
            
            db.session.commit()
            
            return SendToQC(
                success=True, 
                message=f"Order {selected_order['order_number']} successfully sent to QC.",
                qc_logs=qc_logs_created
            )
            
        except Exception as e:
            db.session.rollback()
            return SendToQC(success=False, message=f"Error: {str(e)}")

class UpdateQCStatus(graphene.Mutation):
    class Arguments:
        qc_log_id = graphene.Int(required=True)
        qc_status = graphene.String(required=True)  # PASSED, FAILED
        qc_notes = graphene.String()
        processed_by = graphene.String()

    success = graphene.Boolean()
    message = graphene.String()
    qc_log = graphene.Field(QCLogType)

    def mutate(self, info, qc_log_id, qc_status, qc_notes=None, processed_by=None):
        qc_log = QCLog.query.get(qc_log_id)
        if not qc_log:
            return UpdateQCStatus(success=False, message="QC Log not found.")
        
        if qc_status.upper() not in ['PASSED', 'FAILED']:
            return UpdateQCStatus(success=False, message="Invalid QC status. Use PASSED or FAILED.")
        
        qc_log.qc_status = qc_status.upper()
        qc_log.qc_notes = qc_notes
        qc_log.processed_by = processed_by
        
        db.session.commit()
        
        return UpdateQCStatus(
            success=True, 
            message="QC status updated successfully.",
            qc_log=qc_log
        )

class ReserveStock(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int(required=True)
        items = graphene.List(graphene.String, required=True)  # JSON string items

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, order_id, items):
        try:
            for item_data in items:
                item_info = json.loads(item_data)
                item_code = item_info['item_code']
                quantity = item_info['quantity']
                
                item = Item.query.filter_by(item_code=item_code).first()
                if not item:
                    return ReserveStock(success=False, message=f"Item {item_code} not found.")
                
                if item.available_quantity < quantity:
                    return ReserveStock(success=False, message=f"Insufficient stock for {item_code}.")
                
                item.reserved_quantity += quantity
            
            db.session.commit()
            return ReserveStock(success=True, message="Stock reserved successfully.")
            
        except Exception as e:
            db.session.rollback()
            return ReserveStock(success=False, message=str(e))

class Mutation(graphene.ObjectType):
    create_item = CreateItem.Field()
    update_item = UpdateItem.Field()
    delete_item = DeleteItem.Field()
    send_to_qc = SendToQC.Field()
    update_qc_status = UpdateQCStatus.Field()
    reserve_stock = ReserveStock.Field()

# Menambahkan GraphQL endpoint
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=graphene.Schema(query=Query, mutation=Mutation), graphiql=True))

# REST API endpoints untuk integrasi dengan order service
@app.route('/', methods=['GET'])
def list_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items', methods=['GET'])
def get_all_items():
    """REST endpoint untuk order service mengambil semua items"""
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/api/items/<item_code>/stock', methods=['GET'])
def get_item_stock(item_code):
    """REST endpoint untuk order service cek stock item"""
    item = Item.query.filter_by(item_code=item_code).first()
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    return jsonify({
        'item_code': item.item_code,
        'stock_quantity': item.stock_quantity,
        'reserved_quantity': item.reserved_quantity,
        'available_quantity': item.available_quantity
    })

@app.route('/api/check-availability', methods=['POST'])
def check_availability():
    """REST endpoint untuk order service cek ketersediaan multiple items"""
    try:
        data = request.get_json()
        items_to_check = data.get('items', [])
        
        availability_details = []
        all_available = True
        
        for item_check in items_to_check:
            item_code = item_check['item_code']
            requested_quantity = item_check['requested_quantity']
            
            item = Item.query.filter_by(item_code=item_code).first()
            
            if not item:
                availability_details.append({
                    'item_code': item_code,
                    'available': False,
                    'message': 'Item not found',
                    'stock_quantity': 0,
                    'requested_quantity': requested_quantity
                })
                all_available = False
            elif item.available_quantity < requested_quantity:
                availability_details.append({
                    'item_code': item_code,
                    'available': False,
                    'message': 'Insufficient stock',
                    'stock_quantity': item.available_quantity,
                    'requested_quantity': requested_quantity
                })
                all_available = False
            else:
                availability_details.append({
                    'item_code': item_code,
                    'available': True,
                    'message': 'Available',
                    'stock_quantity': item.available_quantity,
                    'requested_quantity': requested_quantity
                })
        
        return jsonify({
            'available': all_available,
            'message': 'All items available' if all_available else 'Some items unavailable',
            'details': availability_details
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/reserve-stock', methods=['POST'])
def reserve_stock_rest():
    """REST endpoint untuk order service reserve stock"""
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        items = data.get('items', [])
        
        for item_data in items:
            item_code = item_data['item_code']
            quantity = item_data['quantity']
            
            item = Item.query.filter_by(item_code=item_code).first()
            if not item:
                return jsonify({'success': False, 'message': f'Item {item_code} not found'}), 404
            
            if item.available_quantity < quantity:
                return jsonify({'success': False, 'message': f'Insufficient stock for {item_code}'}), 400
            
            item.reserved_quantity += quantity
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Stock reserved successfully',
            'order_id': order_id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'inventory-service'})

# Menjalankan aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat semua tabel sebelum aplikasi dijalankan
    app.run(host='0.0.0.0', port=5000, debug=True)