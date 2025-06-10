from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(50))
    min_stor = db.Column(db.Integer)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi satu-ke-banyak dengan Order
    orders = db.relationship('Order', back_populates='item', lazy=True)

    def to_dict(self):
        return {
            'item_id': self.item_id,
            'item_code': self.item_code,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'min_stor': self.min_stor,
            'location': self.location,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime if needed
        }

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))
    status = db.Column(db.String(50), default="pending")  # Default status is "pending"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi dengan Item (item_id di Order akan menjadi foreign key yang merujuk ke item_id di Item)
    item = db.relationship('Item', back_populates='orders')

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'reference': self.reference,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime if needed
        }
