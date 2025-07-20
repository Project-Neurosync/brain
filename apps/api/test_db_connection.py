#!/usr/bin/env python3
"""
Simple database connection test
"""

import psycopg2
import os
from config.settings import get_settings

def test_connection():
    """Test direct database connection"""
    print("=== Database Connection Test ===")
    
    settings = get_settings()
    db_url = settings.database_url
    
    print(f"Testing connection to: {db_url}")
    
    try:
        # Test connection with shorter timeout
        conn = psycopg2.connect(
            db_url,
            connect_timeout=10  # 10 second timeout
        )
        print("✅ Connection successful!")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        print("✅ Connection closed successfully")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        
        # Check if it's a password issue
        if "authentication failed" in str(e).lower():
            print("💡 This looks like a password issue. Check your DATABASE_URL password.")
        elif "timeout" in str(e).lower():
            print("💡 Connection timeout. This could be:")
            print("   - Network/firewall blocking the connection")
            print("   - Supabase database is paused/sleeping")
            print("   - Wrong host/port in connection string")
        elif "does not exist" in str(e).lower():
            print("💡 Database doesn't exist. Check your database name.")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_connection()
