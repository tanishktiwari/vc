"""
Script to initialize PostgreSQL database for video conferencing application.
Run this script once to set up the database schema.
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'video_conferencing'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }

def create_database():
    """Create the database if it doesn't exist."""
    config = get_db_config()
    db_name = config.pop('database')
    
    try:
        # Connect to postgres database to create new database
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {db_name}')
            print(f"✅ Database '{db_name}' created successfully!")
        else:
            print(f"ℹ️  Database '{db_name}' already exists.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        raise

def init_schema():
    """Initialize database schema by running SQL file."""
    config = get_db_config()
    
    try:
        # Read and execute schema.sql
        with open('database/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Execute schema
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Database schema initialized successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error initializing schema: {e}")
        raise
    except FileNotFoundError:
        print("❌ Error: database/schema.sql file not found!")
        raise

if __name__ == '__main__':
    print("🚀 Initializing PostgreSQL database...")
    print("-" * 50)
    
    try:
        create_database()
        init_schema()
        print("-" * 50)
        print("✅ Database setup completed successfully!")
    except Exception as e:
        print("-" * 50)
        print(f"❌ Database setup failed: {e}")
        exit(1)


