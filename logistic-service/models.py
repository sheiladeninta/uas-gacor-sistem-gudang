from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Shipment(db.Model):
    __tablename__ = 'shipments'
    
    id = db.Column(db.Integer, primary_key=True)
    qc_id = db.Column(db.Integer, nullable=False)  # Reference to QC check
    order_id = db.Column(db.Integer, nullable=False)  # Reference to order
    status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered
    shipping_address = db.Column(db.String(255))
    shipping_service = db.Column(db.String(50))
    weight = db.Column(db.Float)
    shipping_date = db.Column(db.DateTime)
    tracking_number = db.Column(db.String(50))  # DITAMBAHKAN
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'qc_id': self.qc_id,
            'order_id': self.order_id,
            'status': self.status,
            'shipping_address': self.shipping_address,
            'shipping_service': self.shipping_service,
            'weight': self.weight,
            'shipping_date': self.shipping_date.isoformat() if self.shipping_date else None,
            'tracking_number': self.tracking_number,  # DITAMBAHKAN
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
