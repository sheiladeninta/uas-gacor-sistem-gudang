# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), nullable=False, unique=True)  # Item code
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20))  # Satuan barang
    min_stor = db.Column(db.Integer)  # Batas minimum stok
    location = db.Column(db.String(100))  # Lokasi barang
    def __repr__(self):
        return f'<InventoryItem {self.name}>'

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    log_type = db.Column(db.String(50))  # 'inbound' or 'outbound'
    quantity = db.Column(db.Integer)
    reference = db.Column(db.String(100))  # Reference like order number
    created_at = db.Column(db.DateTime)
    created_by = db.Column(db.Integer)  # User ID of who created this log

    item = db.relationship('InventoryItem', backref=db.backref('inventory_logs', lazy=True))

    def __repr__(self):
        return f'<InventoryLog {self.log_type} - Item {self.item_id}>'

class InventoryStatus(db.Model):
    __tablename__ = 'inventory_status'
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), primary_key=True)
    current_stock = db.Column(db.Integer)  # Current available stock
    last_updated = db.Column(db.DateTime)  # Time when stock was last updated
    
    item = db.relationship('InventoryItem', backref=db.backref('inventory_status', lazy=True))

    def __repr__(self):
        return f'<InventoryStatus Item {self.item_id} - Stock {self.current_stock}>'
