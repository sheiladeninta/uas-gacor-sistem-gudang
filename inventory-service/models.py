# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), nullable=False, unique=True)
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
    log_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    log_type = db.Column(db.String(50))  # 'request', 'approve', 'outbound', etc.
    quantity = db.Column(db.Integer)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)
    status = db.Column(db.String(50), default="pending")  # 'pending', 'approved', 'rejected'

    item = db.relationship('InventoryItem', backref=db.backref('inventory_logs', lazy=True))

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
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), primary_key=True)
    current_stock = db.Column(db.Integer)
    last_updated = db.Column(db.DateTime)

    item = db.relationship('InventoryItem', backref=db.backref('inventory_status', lazy=True))

    def __repr__(self):
        return f'<InventoryStatus Item {self.item_id} - Stock {self.current_stock}>'

    # Menambahkan method serialize untuk mengonversi objek menjadi format JSON
    def serialize(self):
        return {
            'item_id': self.item_id,
            'current_stock': self.current_stock,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

