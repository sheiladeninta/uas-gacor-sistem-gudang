from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import uuid

db = SQLAlchemy()

class OrderStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class OrderPriority(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    restaurant_id = db.Column(db.String(100), nullable=False, index=True)
    restaurant_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    priority = db.Column(db.Enum(OrderPriority), default=OrderPriority.NORMAL, nullable=False)
    total_items = db.Column(db.Integer, default=0)
    total_quantity = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    # Dates
    requested_date = db.Column(db.DateTime, nullable=False)
    approved_date = db.Column(db.DateTime)
    processing_date = db.Column(db.DateTime)
    shipped_date = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)
    rejected_date = db.Column(db.DateTime)
    cancelled_date = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(100))
    updated_by = db.Column(db.String(100))
    
    # Contact Information
    contact_person = db.Column(db.String(200))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(200))
    
    # Delivery Information
    delivery_address = db.Column(db.Text)
    delivery_notes = db.Column(db.Text)
    estimated_delivery_date = db.Column(db.DateTime)
    actual_delivery_date = db.Column(db.DateTime)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'restaurant_id': self.restaurant_id,
            'restaurant_name': self.restaurant_name,
            'status': self.status.value,
            'priority': self.priority.value,
            'total_items': self.total_items,
            'total_quantity': self.total_quantity,
            'notes': self.notes,
            'requested_date': self.requested_date.isoformat() if self.requested_date else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'contact_email': self.contact_email,
            'delivery_address': self.delivery_address,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    item_code = db.Column(db.String(50), nullable=False, index=True)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100))
    requested_quantity = db.Column(db.Integer, nullable=False)
    approved_quantity = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00)
    total_price = db.Column(db.Numeric(10, 2), default=0.00)
    notes = db.Column(db.Text)
    
    # Quality Control
    quality_check_required = db.Column(db.Boolean, default=False)
    quality_check_passed = db.Column(db.Boolean, default=None)
    quality_notes = db.Column(db.Text)
    
    # Inventory tracking
    allocated_quantity = db.Column(db.Integer, default=0)
    picked_quantity = db.Column(db.Integer, default=0)
    shipped_quantity = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.item_code}: {self.requested_quantity} {self.unit}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_code': self.item_code,
            'item_name': self.item_name,
            'item_category': self.item_category,
            'requested_quantity': self.requested_quantity,
            'approved_quantity': self.approved_quantity,
            'allocated_quantity': self.allocated_quantity,
            'picked_quantity': self.picked_quantity,
            'shipped_quantity': self.shipped_quantity,
            'unit': self.unit,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'total_price': float(self.total_price) if self.total_price else 0.0,
            'notes': self.notes,
            'quality_check_required': self.quality_check_required,
            'quality_check_passed': self.quality_check_passed,
            'quality_notes': self.quality_notes
        }

class OrderStatusHistory(db.Model):
    __tablename__ = 'order_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    previous_status = db.Column(db.Enum(OrderStatus))
    new_status = db.Column(db.Enum(OrderStatus), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    changed_by = db.Column(db.String(100))
    reason = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.order_id}: {self.previous_status} -> {self.new_status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'previous_status': self.previous_status.value if self.previous_status else None,
            'new_status': self.new_status.value,
            'changed_at': self.changed_at.isoformat(),
            'changed_by': self.changed_by,
            'reason': self.reason,
            'notes': self.notes
        }