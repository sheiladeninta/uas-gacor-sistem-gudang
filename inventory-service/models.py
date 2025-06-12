from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    __table_args__ = {'extend_existing': True}  # Menambahkan extend_existing jika perlu

    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False) 
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20))
    min_stor = db.Column(db.Integer)
    location = db.Column(db.String(100))

    def __repr__(self):
        return f'<InventoryItem {self.name}>'

    # Menambahkan method serialize untuk mengonversi objek menjadi format JSON
    def serialize(self):
        return {
            'id': self.id,
            'item_code': self.item_code,
            'name': self.name,
            'quantity': self.quantity,
            'description': self.description,
            'unit': self.unit,
            'min_stor': self.min_stor,
            'location': self.location
        }


class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    __table_args__ = {'extend_existing': True}  # Menambahkan extend_existing jika perlu
    
    log_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    log_type = db.Column(db.String(50))
    quantity = db.Column(db.Integer)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Menambahkan default datetime
    created_by = db.Column(db.Integer)
    status = db.Column(db.String(50), nullable=False, default="pending")

    item = db.relationship('InventoryItem', backref=db.backref('logs', lazy=True))

    def __repr__(self):
        return f'<InventoryLog {self.log_type} - Item {self.item_id}>'

    def serialize(self):
        return {
            'log_id': self.log_id,
            'item_id': self.item_id,
            'log_type': self.log_type,
            'quantity': self.quantity,
            'reference': self.reference,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by
        }

class InventoryStatus(db.Model):
    __tablename__ = 'inventory_status'
    __table_args__ = {'extend_existing': True}  # Menambahkan extend_existing jika perlu
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    current_stock = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship('InventoryItem', backref=db.backref('inventory_status', lazy=True))

    def __repr__(self):
        return f'<InventoryStatus Item {self.item_id} - Stock {self.current_stock}>'

    def serialize(self):
        return {
            'item_id': self.item_id,
            'current_stock': self.current_stock,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
