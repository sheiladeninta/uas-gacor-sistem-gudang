from app import db  # Mengimpor db dari app.py
from datetime import datetime

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    stock_quantity = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp(), nullable=False)
    
    def __repr__(self):
        return f'<Item {self.item_code}: {self.name}>'
    
    def to_dict(self):
        """ Mengonversi model ke dictionary dengan camelCase untuk GraphQL """
        return {
            'id': self.id,
            'itemCode': self.item_code,  # Ganti 'item_code' ke 'itemCode' sesuai dengan GraphQL camelCase
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'unit': self.unit,
            'unitPrice': float(self.unit_price) if self.unit_price else 0.0,  # Ganti 'unit_price' ke 'unitPrice'
            'stockQuantity': self.stock_quantity,  # Ganti 'stock_quantity' ke 'stockQuantity'
            'createdAt': self.created_at.isoformat(),  # Ganti 'created_at' ke 'createdAt'
            'updatedAt': self.updated_at.isoformat(),  # Ganti 'updated_at' ke 'updatedAt'
        }

    def update_stock(self, quantity):
        """ Update the stock quantity of an item. """
        self.stock_quantity += quantity

# Model QCLog untuk mencatat pengiriman barang ke QC
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
