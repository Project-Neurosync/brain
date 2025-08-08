#!/usr/bin/env python3
"""
Database schema fix script for NeuroSync
Ensures the document_metadata column exists in the documents table
"""

import os
import sys
import asyncio
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import get_db_engine

async def check_and_fix_document_schema():
    """Check if document_metadata column exists and add it if missing."""
    
    engine = get_db_engine()
    
    try:
        with engine.connect() as conn:
            # Check if the column exists
            inspector = inspect(engine)
            columns = inspector.get_columns('documents')
            column_names = [col['name'] for col in columns]
            
            print(f"Current columns in documents table: {column_names}")
            
            if 'document_metadata' not in column_names:
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
                
            # Verify the fix
            inspector = inspect(engine)
            columns = inspector.get_columns('documents')
            column_names = [col['name'] for col in columns]
            
            if 'document_metadata' in column_names:
                print("✅ Schema verification passed")
                return True
            else:
                print("❌ Schema verification failed")
                return False
                
    except SQLAlchemyError as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Checking and fixing document schema...")
    
    # Run the schema fix
    success = asyncio.run(check_and_fix_document_schema())
    
    if success:
        print("🎉 Document schema is ready!")
        sys.exit(0)
    else:
        print("💥 Failed to fix document schema")
        sys.exit(1)
