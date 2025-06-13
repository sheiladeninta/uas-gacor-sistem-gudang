from flask_sqlalchemy import SQLAlchemy
from enum import Enum

db = SQLAlchemy()

class UserRole(Enum):
    STAFF = 'staff'
    CLIENT = 'client'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=True)  # Tetap ada untuk kompatibilitas dengan staff
    username = db.Column(db.String(50), unique=True, nullable=True)  # Username untuk login client
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(10), nullable=False, default=UserRole.CLIENT.value)
    email = db.Column(db.String(120), unique=True, nullable=True)
    companyName = db.Column(db.String(200), nullable=True)  # Nama perusahaan untuk client
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    
    def __repr__(self):
        return f'<User {self.nama or self.username} ({self.role})>'