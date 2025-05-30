from db import db

class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'
    log_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    log_type = db.Column(db.Enum('inbound', 'outbound', name='log_type_enum'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(100))
    created_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
