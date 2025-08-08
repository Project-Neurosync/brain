#!/usr/bin/env python3
"""
Quick database fix for NeuroSync - Add missing document_metadata column
"""

import os
import sys
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database URL from environment (Supabase)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.lahkhtewrqlqcfhpytqo:Moksh_mdg40@aws-0-ap-south-1.pooler.supabase.com:5432/postgres")

def fix_database_schema():
    """Add the missing document_metadata column."""
    
    try:
        print(f"🔗 Connecting to database...")
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("✅ Connected to database successfully")
            
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents' 
                AND column_name = 'document_metadata';
            """))
            
            if result.fetchone() is None:
                print("❌ document_metadata column is missing!")
                print("Adding document_metadata column...")
                
                # Add the missing column
                conn.execute(text("""
                    ALTER TABLE documents 
                    ADD COLUMN document_metadata JSONB;
                """))
                conn.commit()
                
                print("✅ Successfully added document_metadata column")
            else:
                print("✅ document_metadata column already exists")
                
        print("🎉 Database schema is ready!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("💡 Make sure your Supabase database is accessible")
        return False

if __name__ == "__main__":
    print("🔧 Fixing database schema...")
    success = fix_database_schema()
    sys.exit(0 if success else 1)
