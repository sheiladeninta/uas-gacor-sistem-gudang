import collections
import collections.abc
collections.Mapping = collections.abc.Mapping
collections.Iterable = collections.abc.Iterable
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime

import graphene
from graphene_sqlalchemy import SQLAlchemyObjectType
from graphene import ObjectType
from flask_graphql import GraphQLView
from config import Config
from flask_cors import CORS


# Inisialisasi Flask app
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


# Model Item
class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False, default="pcs")  # Menambahkan nilai default
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    stock_quantity = db.Column(db.Integer, default=0)

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
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def update_stock(self, quantity):
        self.stock_quantity += quantity

class QCLog(db.Model):
    __tablename__ = 'qc_logs'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)  # ID order yang dikirim ke QC
    item_code = db.Column(db.String(50), nullable=False)  # Kode barang
    item_name = db.Column(db.String(200), nullable=False)  # Nama barang
    quantity = db.Column(db.Integer, nullable=False)  # Jumlah barang yang dikirim ke QC
    sent_to_qc_at = db.Column(db.DateTime, default=datetime.utcnow)  # Waktu pengiriman ke QC

    def __repr__(self):
        return f"<QCLog {self.item_code}: {self.item_name}, Quantity: {self.quantity}>"

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'quantity': self.quantity,
            'sent_to_qc_at': self.sent_to_qc_at.isoformat()
        }

# Model OrderRequest
class OrderRequest(db.Model):
    __tablename__ = 'order_requests'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(50), unique=True, nullable=False)
    item_code = db.Column(db.String(50), db.ForeignKey('items.item_code'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Status: Pending, Sent to QC, etc.

    item = db.relationship("Item", backref=db.backref("orders", lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'order_code': self.order_code,
            'item_code': self.item_code,
            'quantity': self.quantity,
            'status': self.status
        }


# GraphQL schema untuk Item
class ItemType(SQLAlchemyObjectType):
    class Meta:
        model = Item
        fields = ('id', 'item_code', 'name', 'description', 'category', 'unit', 'unit_price', 'stock_quantity', 'created_at', 'updated_at')


# GraphQL schema untuk OrderRequest
class OrderRequestType(SQLAlchemyObjectType):
    class Meta:
        model = OrderRequest
        fields = ('id', 'order_code', 'item_code', 'quantity', 'status')

class QCLogType(SQLAlchemyObjectType):
    class Meta:
        model = QCLog
        fields = ('id', 'order_id', 'item_code', 'item_name', 'quantity', 'sent_to_qc_at')  # Sesuaikan field dengan yang ada di QCLog


# Query untuk mendapatkan semua item dan order request
class Query(graphene.ObjectType):
    items = graphene.List(ItemType)
    order_requests = graphene.List(OrderRequestType)
    qc_logs = graphene.List(QCLogType)  # Mendapatkan semua log QC

    def resolve_items(self, info):
        return Item.query.all()

    def resolve_qc_logs(self, info):
        return QCLog.query.all()
    
    def resolve_order_requests(self, info):
        return OrderRequest.query.all()


# Mutation untuk mengirim barang ke QC dan mengupdate stok
from datetime import datetime

# Mutasi untuk mengirim barang ke QC dan mencatatnya di tabel qc_logs
class SendToQC(graphene.Mutation):
    class Arguments:
        order_id = graphene.Int(required=True)
        item_code = graphene.String(required=True)
        item_name = graphene.String(required=True)
        quantity = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, order_id, item_code, item_name, quantity):
        item = Item.query.filter_by(item_code=item_code).first()
        if not item:
            return SendToQC(success=False, message="Item tidak ditemukan.")
        if item.stock_quantity < quantity:
            return SendToQC(success=False, message="Stok tidak cukup.")

        # Kurangi stok
        item.stock_quantity -= quantity

        # Tambahkan ke QCLog
        qc_log = QCLog(
            order_id=order_id,
            item_code=item_code,
            item_name=item_name,
            quantity=quantity
        )
        db.session.add(qc_log)
        db.session.commit()

        return SendToQC(success=True, message="Berhasil dikirim ke QC dan stok dikurangi.")

# Tambahkan ke Mutation

    


# Mutation untuk Create, Update dan Delete item
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

    def mutate(self, info, item_code, name, stock_quantity, description, unit=None, category=None, unit_price=0.0):
        if unit is None:
            unit = "pcs"
        if category is None:
            category = "Uncategorized"
        if unit_price is None:
            unit_price = 0.0

        existing_item = Item.query.filter_by(item_code=item_code).first()
        if existing_item:
            raise graphene.GraphQLError(f"Item with item_code '{item_code}' already exists.")

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
        return CreateItem(item=new_item)


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

    def mutate(self, info, item_code, name=None, stock_quantity=None, description=None, unit=None, category=None, unit_price=None):
        item = Item.query.filter_by(item_code=item_code).first()
        if not item:
            raise Exception(f"Item with item_code '{item_code}' not found.")

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
        
        item = Item.query.filter_by(item_code=item_code).first()
        if not item:
            raise Exception(f"Item with item_code '{item_code}' not found.")
        
        # Mengurangi stok
        item.stock_quantity -= stock_quantity

        db.session.commit()

        return UpdateItem(item=item)


class DeleteItem(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    def mutate(self, info, id):
        item = Item.query.get(id)
        if not item:
            raise Exception(f"Item with id '{id}' not found.")

        db.session.delete(item)
        db.session.commit()

        return DeleteItem(success=True)

class UpdateInventoryStock(graphene.Mutation):
    class Arguments:
        item_code = graphene.String(required=True)
        quantity = graphene.Int(required=True)
    
    item = graphene.Field(ItemType)
    success = graphene.Boolean()

    def mutate(self, info, item_code, quantity):
        item = Item.query.filter_by(item_code=item_code).first()
        if not item:
            raise Exception(f"Item with item_code '{item_code}' not found.")
        
        # Update stock
        item.stock_quantity -= quantity
        if item.stock_quantity < 0:
            raise Exception("Insufficient stock")
        
        db.session.commit()

        return UpdateInventoryStock(item=item, success=True)

class UpdateInventoryForQC(graphene.Mutation):
    class Arguments:
        item_code = graphene.String(required=True)
        quantity = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, item_code, quantity):
        try:
            item = Item.query.filter_by(item_code=item_code).first()
            if not item:
                raise Exception(f"Item with item_code {item_code} not found.")
            
            # Decrease stock quantity
            if item.stock_quantity < quantity:
                raise Exception("Not enough stock to fulfill the request.")
            
            item.stock_quantity -= quantity
            db.session.commit()

            return UpdateInventoryForQC(success=True, message="Inventory updated successfully.")
        except Exception as e:
            db.session.rollback()
            return UpdateInventoryForQC(success=False, message=str(e))



class Mutation(graphene.ObjectType):
    create_item = CreateItem.Field()
    update_item = UpdateItem.Field()
    delete_item = DeleteItem.Field()
    send_to_qc = SendToQC.Field()
    update_inventory_stock = UpdateInventoryStock.Field()
    update_inventory_for_qc = UpdateInventoryForQC.Field()


# Menambahkan GraphQL endpoint
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=graphene.Schema(query=Query, mutation=Mutation), graphiql=True))

@app.route('/', methods=['GET'])
def list_items():
    items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

# Menjalankan aplikasi
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Membuat semua tabel sebelum aplikasi dijalankan
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
