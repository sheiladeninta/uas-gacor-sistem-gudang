import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Service URLs for microservices communication
    INVENTORY_SERVICE_URL = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001')
    USER_SERVICE_URL = os.getenv('USER_SERVICE_URL', 'http://user-service:5000')
    ITEM_SERVICE_URL = os.getenv('ITEM_SERVICE_URL', 'http://item-service:5003')
    QUALITY_CONTROL_SERVICE_URL = os.getenv('QUALITY_CONTROL_SERVICE_URL', 'http://quality-control-service:5004')
    
    # API Configuration
    API_TITLE = 'Order Service API'
    API_VERSION = 'v1'
    
    # CORS Configuration
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:8080', 'http://frontend:3000']
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Request timeout for inter-service communication
    REQUEST_TIMEOUT = 30

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///order_service_dev.db'
    )
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://user:password@db:5432/order_service'
    )
    SQLALCHEMY_ECHO = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class testingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': testingConfig,
    'default': DevelopmentConfig
}