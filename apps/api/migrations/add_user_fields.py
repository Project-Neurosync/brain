"""
Database Migration: Add missing User model fields
Adds password_hash, monthly_token_quota, bonus_tokens, and user_metadata columns
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from config.settings import get_settings

def run_migration():
    """Add missing columns to the users table"""
    settings = get_settings()
    
    print("🔄 Starting database migration...")
    print(f"Database URL: {settings.database_url}")
    
    try:
        # Create database engine
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Check if columns already exist
            inspector = inspect(engine)
            existing_columns = inspector.get_columns('users')
            existing_column_names = [col['name'] for col in existing_columns]
            
            print(f"📋 Existing columns: {existing_column_names}")
            
            # Add missing columns
            migrations = []
            
            if 'password_hash' not in existing_column_names:
                migrations.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NULL")
                
            if 'monthly_token_quota' not in existing_column_names:
                migrations.append("ALTER TABLE users ADD COLUMN monthly_token_quota INTEGER DEFAULT 200")
                
            if 'bonus_tokens' not in existing_column_names:
                migrations.append("ALTER TABLE users ADD COLUMN bonus_tokens INTEGER DEFAULT 0")
                
            if 'user_metadata' not in existing_column_names:
                migrations.append("ALTER TABLE users ADD COLUMN user_metadata JSONB DEFAULT '{}'")
            
            # Run migrations
            if migrations:
                print(f"🔧 Running {len(migrations)} migrations...")
                for i, migration in enumerate(migrations, 1):
                    print(f"  {i}. {migration}")
                    conn.execute(text(migration))
                    
                # Commit the changes
                conn.commit()
                print("✅ Database migration completed successfully!")
            else:
                print("ℹ️ No migrations needed - all columns already exist")
                
            # Verify the changes
            updated_columns = inspector.get_columns('users')
            
            print("\n📊 Updated table structure:")
            for col in updated_columns:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                default = f" DEFAULT {col['default']}" if col['default'] is not None else ""
                print(f"  - {col['name']}: {col['type']} {nullable}{default}")
                
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration()
