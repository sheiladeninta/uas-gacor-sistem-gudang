from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Inisialisasi Flask dan SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qc_service.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class QCLog(db.Model):
    __tablename__ = 'qc_logs'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), nullable=False)
    item_code = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)  # Make sure 'item_name' is here
    requested_quantity = db.Column(db.Integer, nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="PENDING")  # Example status
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QCLog {self.order_number} - {self.item_code}>'

    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'item_code': self.item_code,
            'item_name': self.item_name,  # Ensure 'item_name' is included here
            'requested_quantity': self.requested_quantity,
            'unit': self.unit,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
        }


