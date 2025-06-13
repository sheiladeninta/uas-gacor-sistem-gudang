import os

class Config:
    # Get the directory containing this file
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'qc_items.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-qc-service'
    DEBUG = True
    
    # JWT configuration
    JWT_SECRET_KEY = 'your-secret-key'  # Change this in production
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # Path ke database inventory service
    INVENTORY_DB_PATH = '../inventory-service/instance/inventory-service.db'
    
    # Inventory Service
    INVENTORY_SERVICE_URL = 'http://localhost:5001'  # Sesuaikan dengan port inventory service
    
    # Ensure instance folder exists
    @staticmethod
    def init_app(app):
        instance_path = os.path.join(os.path.dirname(__file__), 'instance')
        if not os.path.exists(instance_path):
            os.makedirs(instance_path) 