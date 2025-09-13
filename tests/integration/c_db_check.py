#!/usr/bin/env python3
"""
Database Schema Verification Script
Quick verification that database schema is properly configured.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# Add ETL src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../services/etl'))

try:
    from src.config import get_settings
except ImportError:
    print("❌ Could not import ETL config. Make sure you're in the correct directory.")
    sys.exit(1)

def verify_schema():
    """Verify database schema and basic data"""
    print("🔍 Verifying Database Schema...")
    
    settings = get_settings()
    
    try:
        conn = psycopg2.connect(settings.database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'anime_snapshots'
            );
        """)
        
        if not cursor.fetchone()['exists']:
            print("❌ anime_snapshots table does not exist!")
            return False
        
        print("✅ anime_snapshots table exists")
        
        # Check required columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'anime_snapshots'
            ORDER BY ordinal_position;
        """)
        columns = [row['column_name'] for row in cursor.fetchall()]
        
        required = ['id', 'mal_id', 'title', 'snapshot_type', 'snapshot_date', 'score']
        missing = [col for col in required if col not in columns]
        
        if missing:
            print(f"❌ Missing columns: {missing}")
            return False
        
        print(f"✅ Schema valid ({len(columns)} columns)")
        
        # Check data
        cursor.execute("SELECT COUNT(*) as total FROM anime_snapshots;")
        total = cursor.fetchone()['total']
        print(f"📊 Total records: {total}")
        
        if total > 0:
            # Sample data by type
            cursor.execute("""
                SELECT snapshot_type, COUNT(*) as count 
                FROM anime_snapshots 
                GROUP BY snapshot_type 
                ORDER BY count DESC;
            """)
            
            print("📈 Data distribution:")
            for row in cursor.fetchall():
                print(f"  - {row['snapshot_type']}: {row['count']} records")
            
            # Top scoring anime
            cursor.execute("""
                SELECT title, score, rank FROM anime_snapshots 
                WHERE score IS NOT NULL 
                ORDER BY score DESC NULLS LAST 
                LIMIT 3;
            """)

        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main verification function"""
    print("=" * 60)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 60)
    
    success = verify_schema()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ DATABASE VERIFICATION SUCCESSFUL!")
        print("Your database is ready for the ETL pipeline.")
    else:
        print("❌ DATABASE VERIFICATION FAILED!")
        print("Please check your database setup.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()