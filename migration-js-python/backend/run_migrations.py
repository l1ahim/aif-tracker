#!/usr/bin/env python3
"""
Database migration script for AIF Tracker
Run this to create or update database tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from models import Base

def load_env_file(file_path='.env'):
    """Load environment variables from .env file."""
    if not os.path.exists(file_path):
        return False
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key] = value
        return True
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

def get_database_url():
    """Get database URL from environment variables."""
    
    # Load .env file first
    load_env_file()
    
    # Try to get full DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # If not available, construct from individual components
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'aif_tracker')
    db_user = os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres'))
    db_password = os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
    
    if not db_password:
        print("✗ No database password found in .env file")
        print("Please add DB_PASSWORD=your_password to your .env file")
        return None
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def run_migrations():
    """Run database migrations."""
    
    database_url = get_database_url()
    if not database_url:
        return False
    
    # Mask password in logs
    safe_url = database_url.split('@')[1] if '@' in database_url else 'local'
    print(f"Connecting to database: {safe_url}")
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            
            # Check if transactions table exists and needs migration
            result = connection.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'transactions' AND column_name = 'id'
            """))
            
            existing_id_type = None
            for row in result:
                existing_id_type = row[0]
                break
            
            if existing_id_type == 'integer':
                print("⚠️  Found integer ID column, migrating to UUID...")
                
                # Drop and recreate table with UUID (backup data first if needed)
                connection.execute(text("DROP TABLE IF EXISTS transactions_backup"))
                connection.execute(text("CREATE TABLE transactions_backup AS SELECT * FROM transactions"))
                connection.execute(text("DROP TABLE transactions"))
                
                # Create new table with UUID
                Base.metadata.create_all(bind=engine)
                
                print("✓ Migrated ID column from integer to UUID")
            elif existing_id_type == 'uuid':
                print("✓ ID column is already UUID")
            else:
                print("ℹ️  Creating new transactions table with UUID")
                # Create all tables
                Base.metadata.create_all(bind=engine)
        
        print("✓ Database tables created/updated successfully")
        
        # Verify tables exist
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"✓ Tables in database: {', '.join(tables)}")
            
            if 'transactions' in tables:
                print("✓ Transactions table exists")
                
                # Check table structure
                result = connection.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'transactions'
                    ORDER BY ordinal_position
                """))
                columns = [(row[0], row[1]) for row in result]
                print(f"✓ Transactions table columns: {len(columns)} columns")
                for col_name, col_type in columns:
                    print(f"  - {col_name}: {col_type}")
            else:
                print("✗ Transactions table not found")
                return False
                
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify database credentials")
        print("3. Ensure database exists")
        print("4. Check network connectivity")
        return False
    
    print("\n🎉 Migration completed successfully!")
    return True

if __name__ == "__main__":
    print("AIF Tracker Database Migration")
    print("=" * 40)
    success = run_migrations()
    sys.exit(0 if success else 1)
