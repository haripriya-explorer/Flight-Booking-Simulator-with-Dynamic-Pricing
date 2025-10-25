"""
Flight Booking System - Database Configuration
Handles database connection and initialization
"""

import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent.parent / "db" / "flight_booking.db"

def get_db_connection():
    """
    Create a database connection and return it
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

def initialize_database():
    """
    Initialize the database with schema if it doesn't exist
    """
    # Create db directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Check if database already exists
    if os.path.exists(DB_PATH):
        print(f"Database already exists at {DB_PATH}")
        return True
    
    print(f"Creating database at {DB_PATH}")
    
    # Get schema path
    schema_path = Path(__file__).parent.parent / "db" / "db_schema.sql"
    
    if not os.path.exists(schema_path):
        print(f"Schema file not found at {schema_path}")
        return False
    
    # Create database and run schema
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.executescript(schema_sql)
        conn.commit()
        print("Database schema created successfully")
        return True
    except Exception as e:
        print(f"Error creating schema: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Initialize database when script is run directly
    initialize_database()