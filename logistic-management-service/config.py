# config.py
import os
from datetime import datetime

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/logistic-management.db'  # Path ke database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    INVENTORY_SERVICE_URL = 'http://inventory-service-url'