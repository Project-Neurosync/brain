"""
Fix auth_provider_id NOT NULL constraint mismatch
This migration makes auth_provider_id nullable to match the model definition
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import get_settings

def run_migration():
    """Run the migration to fix auth_provider_id constraint"""
    settings = get_settings()
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    print("Starting migration: Fix auth_provider_id NOT NULL constraint...")
    
    try:
        with engine.connect() as connection:
            # Start a transaction
            trans = connection.begin()
            
            try:
                # Check if the column exists and has NOT NULL constraint
                result = connection.execute(text("""
                    SELECT is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'auth_provider_id'
                """))
                
                row = result.fetchone()
                if row and row[0] == 'NO':
                    print("Found NOT NULL constraint on auth_provider_id, removing it...")
                    
                    # Remove NOT NULL constraint from auth_provider_id
                    connection.execute(text("""
                        ALTER TABLE users 
                        ALTER COLUMN auth_provider_id DROP NOT NULL
                    """))
                    
                    print("✓ Successfully removed NOT NULL constraint from auth_provider_id")
                else:
                    print("auth_provider_id is already nullable or column doesn't exist")
                
                # Commit the transaction
                trans.commit()
                print("✓ Migration completed successfully!")
                
            except Exception as e:
                # Rollback on error
                trans.rollback()
                print(f"✗ Migration failed: {e}")
                raise
                
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        raise

if __name__ == "__main__":
    run_migration()
