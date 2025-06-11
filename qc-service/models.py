from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class QualityControl(db.Model):
    """Model untuk pencatatan hasil quality control"""
    __tablename__ = 'quality_control'

    qc_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, nullable=False)
    check_type = db.Column(db.String, nullable=False)  # inbound, stock_audit, outbound
    condition = db.Column(db.String, nullable=False)   # layak, rusak, kedaluwarsa
    quantity_checked = db.Column(db.Integer, nullable=False)
    checked_by = db.Column(db.Integer, nullable=False)
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    batch_number = db.Column(db.String)
    expiry_date = db.Column(db.Date)
    storage_location = db.Column(db.String)
    temperature = db.Column(db.Float)  # Untuk item yang memerlukan kontrol suhu
    humidity = db.Column(db.Float)     # Untuk item yang memerlukan kontrol kelembaban
    action_taken = db.Column(db.String) # Tindakan yang diambil jika ada masalah
    is_approved = db.Column(db.Boolean, default=False)
    approved_by = db.Column(db.Integer)
    approved_at = db.Column(db.DateTime)

    def __init__(self, item_id, check_type, condition, quantity_checked, checked_by, 
                 notes=None, batch_number=None, expiry_date=None, storage_location=None,
                 temperature=None, humidity=None, action_taken=None):
        self.item_id = item_id
        self.check_type = check_type
        self.condition = condition
        self.quantity_checked = quantity_checked
        self.checked_by = checked_by
        self.notes = notes
        self.batch_number = batch_number
        self.expiry_date = expiry_date
        self.storage_location = storage_location
        self.temperature = temperature
        self.humidity = humidity
        self.action_taken = action_taken
