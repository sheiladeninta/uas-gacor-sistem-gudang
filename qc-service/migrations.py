from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from config import Config
import sqlite3
import os
from models import db, QualityControl

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

def run_migrations():
    """Run database migrations"""
    try:
        # Get database path from config
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        
        # Create new database if it doesn't exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Drop existing tables if they exist
        cursor.execute('DROP TABLE IF EXISTS qc_results')
        
        # Create qc_results table with new structure
        cursor.execute('''
        CREATE TABLE qc_results (
            id INTEGER PRIMARY KEY,
            inventory_log_id INTEGER NOT NULL,
            item_code TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            sent_to_logistics BOOLEAN DEFAULT 0,
            sent_to_logistics_at TIMESTAMP,
            returned_to_inventory BOOLEAN DEFAULT 0,
            returned_to_inventory_at TIMESTAMP
        )
        ''')
        
        # Hide ROWID
        cursor.execute('SELECT * FROM qc_results WHERE 0')
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print("Successfully migrated database")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def remove_sqlite_sequence():
    """Remove sqlite_sequence table from the database"""
    try:
        # Get database path from config
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        
        # Only proceed if database exists
        if os.path.exists(db_path):
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Drop sqlite_sequence table
            cursor.execute('DROP TABLE IF EXISTS sqlite_sequence')
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            print("Successfully removed sqlite_sequence table")
            
    except Exception as e:
        print(f"Error removing sqlite_sequence table: {str(e)}")

def add_new_columns():
    """Add new columns for logistics and inventory tracking"""
    try:
        with app.app_context():
            # Add sent_to_logistics column
            db.session.execute(text('ALTER TABLE qc_results ADD COLUMN sent_to_logistics BOOLEAN DEFAULT 0'))
            # Add sent_to_logistics_at column
            db.session.execute(text('ALTER TABLE qc_results ADD COLUMN sent_to_logistics_at TIMESTAMP'))
            # Add returned_to_inventory column
            db.session.execute(text('ALTER TABLE qc_results ADD COLUMN returned_to_inventory BOOLEAN DEFAULT 0'))
            # Add returned_to_inventory_at column
            db.session.execute(text('ALTER TABLE qc_results ADD COLUMN returned_to_inventory_at TIMESTAMP'))
            
            db.session.commit()
            print("Successfully added new columns")
    except Exception as e:
        print(f"Error adding new columns: {str(e)}")
        db.session.rollback()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def upgrade():
    app = create_app()
    with app.app_context():
        # Add new columns
        with db.engine.connect() as conn:
            conn.execute("""
                ALTER TABLE qc_results 
                ADD COLUMN sent_to_logistics BOOLEAN DEFAULT FALSE,
                ADD COLUMN sent_to_logistics_at TIMESTAMP,
                ADD COLUMN returned_to_inventory BOOLEAN DEFAULT FALSE,
                ADD COLUMN returned_to_inventory_at TIMESTAMP;
            """)
            conn.commit()

if __name__ == '__main__':
    run_migrations()
    remove_sqlite_sequence()
    add_new_columns()
    upgrade() 