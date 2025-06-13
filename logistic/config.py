import os
from datetime import timedelta

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///logistic.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Service URLs
    QC_SERVICE_URL = os.getenv('QC_SERVICE_URL', 'http://qc-service:5000')
    ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://order-service:5000')
    
    # Other configurations
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5002))
