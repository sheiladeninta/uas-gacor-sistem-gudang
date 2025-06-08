from db import db

class Item(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.Integer, primary_key=True)
    item_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    unit = db.Column(db.String(20))
    min_stock = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
