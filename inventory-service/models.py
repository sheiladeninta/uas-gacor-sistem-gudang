from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Inisialisasi objek db di models.py
db = SQLAlchemy()

def get_current_time():
    """Mengambil waktu saat ini dalam UTC"""
    return datetime.now(timezone.utc)

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), default='')  # Menambahkan default value untuk description
    created_at = db.Column(db.DateTime, default=get_current_time)  # Menggunakan fungsi untuk default datetime
    updated_at = db.Column(db.DateTime, default=get_current_time, onupdate=get_current_time)  # Menggunakan fungsi untuk onupdate

    def __repr__(self):
        return f'<InventoryItem {self.name}>'

    def __init__(self, name, quantity, description=None):
        """Untuk memastikan bahwa description selalu terisi dengan default='' jika tidak diberikan"""
        self.name = name
        self.quantity = quantity
        self.description = description or ''

    def to_dict(self):
        """Mengubah objek menjadi dictionary untuk JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'quantity': self.quantity,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
