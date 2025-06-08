import os
from urllib.parse import quote_plus

class Config:
    # Path ke database di folder 'instance'
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'inventory-service.db')

    # Pastikan folder 'instance' ada, jika belum, buat folder tersebut
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"  # Gunakan URL encoding untuk path yang mengandung spasi
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')  # Ganti dengan SECRET_KEY yang aman jika di produksi
    print(f"Database path: {db_path}")  # Untuk memastikan path database