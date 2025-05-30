from db import db

class InventoryStatus(db.Model):
    __tablename__ = 'inventory_status'
    item_id = db.Column(db.Integer, primary_key=True)
    current_stock = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
