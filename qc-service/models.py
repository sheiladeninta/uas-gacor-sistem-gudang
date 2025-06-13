from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QualityControl(db.Model):
    """Model untuk menyimpan hasil quality control"""
    __tablename__ = 'qc_results'
    
    id = db.Column(db.Integer, primary_key=True)
    inventory_log_id = db.Column(db.Integer, nullable=False)  # Reference to inventory qc_logs.id
    item_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # Renamed from item_name
    status = db.Column(db.String(20), nullable=False)  # 'approved', 'rejected'
    notes = db.Column(db.Text, nullable=True)
    checked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sent_to_logistics = db.Column(db.Boolean, default=False)  # Track if sent to logistics
    sent_to_logistics_at = db.Column(db.DateTime, nullable=True)  # When it was sent to logistics
    returned_to_inventory = db.Column(db.Boolean, default=False)  # Track if returned to inventory
    returned_to_inventory_at = db.Column(db.DateTime, nullable=True)  # When it was returned to inventory

    def to_dict(self):
        return {
            'id': self.id,
            'inventory_log_id': self.inventory_log_id,
            'item_code': self.item_code,
            'name': self.name,
            'status': self.status,
            'notes': self.notes,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None,
            'sent_to_logistics': self.sent_to_logistics,
            'sent_to_logistics_at': self.sent_to_logistics_at.isoformat() if self.sent_to_logistics_at else None,
            'returned_to_inventory': self.returned_to_inventory,
            'returned_to_inventory_at': self.returned_to_inventory_at.isoformat() if self.returned_to_inventory_at else None
        } 