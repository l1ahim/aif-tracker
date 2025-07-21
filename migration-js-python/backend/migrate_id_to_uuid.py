#!/usr/bin/env python3
"""
Migration script to convert transaction ID from integer to UUID
"""

import os
import sys
from sqlalchemy import create_engine, text

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
                    value = value.strip('"\'')
                    os.environ[key] = value
        return True
    except Exception as e:
        print(f"Error loading .env file: {e}")
        return False

def get_database_url():
    """Get database URL from environment variables."""
    load_env_file()
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'aif_tracker')
    db_user = os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres'))
    db_password = os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
    
    if not db_password:
        print("✗ No database password found")
        return None
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def migrate_to_uuid():
    """Migrate the transactions table ID from integer to UUID."""
    
    database_url = get_database_url()
    if not database_url:
        return False
    
    try:
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Start transaction
            trans = connection.begin()
            
            try:
                print("🔍 Checking current table structure...")
                
                # Check if table exists
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'transactions'
                    )
                """))
                
                table_exists = result.scalar()
                
                if not table_exists:
                    print("ℹ️  Transactions table doesn't exist, creating new one...")
                    connection.execute(text("""
                        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
                        
                        CREATE TABLE transactions (
                            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                            user_id VARCHAR(255) NOT NULL,
                            amount DOUBLE PRECISION NOT NULL,
                            description TEXT,
                            category VARCHAR(100),
                            merchant VARCHAR(255),
                            date TIMESTAMP NOT NULL DEFAULT NOW(),
                            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                            receipt_hash VARCHAR(255),
                            ai_confidence DOUBLE PRECISION,
                            processing_status VARCHAR(50) DEFAULT 'pending',
                            transaction_type VARCHAR(20) NOT NULL DEFAULT 'expense',
                            manually_verified BOOLEAN DEFAULT FALSE
                        );
                        
                        CREATE INDEX idx_transactions_user_id ON transactions(user_id);
                        CREATE INDEX idx_transactions_receipt_hash ON transactions(receipt_hash);
                    """))
                    print("✓ Created new transactions table with UUID")
                else:
                    # Check current ID type
                    result = connection.execute(text("""
                        SELECT data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'transactions' AND column_name = 'id'
                    """))
                    
                    current_type = result.scalar()
                    
                    if current_type == 'uuid':
                        print("✓ ID column is already UUID type")
                        trans.commit()
                        return True
                    
                    print(f"🔄 Converting ID column from {current_type} to UUID...")
                    
                    # Check if there's data in the table
                    result = connection.execute(text("SELECT COUNT(*) FROM transactions"))
                    row_count = result.scalar()
                    
                    if row_count > 0:
                        print(f"⚠️  Found {row_count} existing records, backing up...")
                        
                        # Create backup table
                        connection.execute(text("DROP TABLE IF EXISTS transactions_backup"))
                        connection.execute(text("CREATE TABLE transactions_backup AS SELECT * FROM transactions"))
                        print("✓ Backup created")
                    
                    # Enable UUID extension
                    connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                    
                    # Drop and recreate table with UUID
                    connection.execute(text("DROP TABLE transactions"))
                    
                    connection.execute(text("""
                        CREATE TABLE transactions (
                            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                            user_id VARCHAR(255) NOT NULL,
                            amount DOUBLE PRECISION NOT NULL,
                            description TEXT,
                            category VARCHAR(100),
                            merchant VARCHAR(255),
                            date TIMESTAMP NOT NULL DEFAULT NOW(),
                            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
                            receipt_hash VARCHAR(255),
                            ai_confidence DOUBLE PRECISION,
                            processing_status VARCHAR(50) DEFAULT 'pending',
                            transaction_type VARCHAR(20) NOT NULL DEFAULT 'expense',
                            manually_verified BOOLEAN DEFAULT FALSE
                        );
                        
                        CREATE INDEX idx_transactions_user_id ON transactions(user_id);
                        CREATE INDEX idx_transactions_receipt_hash ON transactions(receipt_hash);
                    """))
                    
                    print("✓ Recreated table with UUID ID column")
                
                # Commit the transaction
                trans.commit()
                print("🎉 Migration completed successfully!")
                return True
                
            except Exception as e:
                trans.rollback()
                print(f"✗ Migration failed, rolling back: {e}")
                return False
                
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("UUID Migration Script")
    print("=" * 30)
    success = migrate_to_uuid()
    sys.exit(0 if success else 1)
