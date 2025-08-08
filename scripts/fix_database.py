#!/usr/bin/env python3
"""
Database fix script for NeuroSync
Adds missing query_metadata column to ai_queries table
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/neurosync')

def apply_database_fixes():
    """Apply database schema fixes"""
    database_url = get_database_url()
    
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password
        )
        
        cursor = conn.cursor()
        
        print("🔧 Applying database fixes...")
        
        # Check if query_metadata column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ai_queries' AND column_name = 'query_metadata'
        """)
        
        if not cursor.fetchone():
            print("📝 Adding query_metadata column to ai_queries table...")
            cursor.execute("""
                ALTER TABLE ai_queries 
                ADD COLUMN query_metadata JSONB
            """)
            print("✅ Added query_metadata column")
        else:
            print("✅ query_metadata column already exists")
        
        # Check if project_metadata column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name = 'project_metadata'
        """)
        
        if not cursor.fetchone():
            print("📝 Adding project_metadata column to projects table...")
            cursor.execute("""
                ALTER TABLE projects 
                ADD COLUMN project_metadata JSONB
            """)
            print("✅ Added project_metadata column")
        else:
            print("✅ project_metadata column already exists")
        
        # Commit changes
        conn.commit()
        print("🎉 Database fixes applied successfully!")
        
    except Exception as e:
        print(f"❌ Error applying database fixes: {e}")
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 NeuroSync Database Fix Script")
    print("=" * 40)
    apply_database_fixes()
