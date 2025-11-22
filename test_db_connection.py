#!/usr/bin/env python3
"""
PostgreSQL Connection Test Script
Tests database connectivity with the provided connection string
"""

import sys
import os
from urllib.parse import urlparse

def test_connection(connection_string: str):
    """Test PostgreSQL connection with the given connection string"""

    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)

    # Parse connection string
    try:
        parsed = urlparse(connection_string)
        print(f"\nConnection Details:")
        print(f"  Host: {parsed.hostname}")
        print(f"  Port: {parsed.port or 5432}")
        print(f"  Database: {parsed.path.lstrip('/')}")
        print(f"  Username: {parsed.username}")
        print(f"  Password: {'*' * len(parsed.password) if parsed.password else '(none)'}")
    except Exception as e:
        print(f"\n[ERROR] Failed to parse connection string: {e}")
        return False

    # Try to import psycopg2
    try:
        import psycopg2
        print("\n[OK] psycopg2 module available")
    except ImportError:
        print("\n[ERROR] psycopg2 not installed. Install with: pip install psycopg2-binary")
        return False

    # Try to connect
    print(f"\n[*] Attempting connection to {parsed.hostname}:{parsed.port or 5432}...")
    try:
        conn = psycopg2.connect(connection_string)
        print("[OK] Connection successful!")

        # Test a simple query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"\n[OK] PostgreSQL Version:")
            print(f"  {version.split(',')[0]}")

            # Check if generations table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'generations'
                );
            """)
            table_exists = cursor.fetchone()[0]

            if table_exists:
                print(f"\n[OK] 'generations' table exists")

                # Count records
                cursor.execute("SELECT COUNT(*) FROM generations;")
                count = cursor.fetchone()[0]
                print(f"  Records in generations table: {count}")
            else:
                print(f"\n[WARN] 'generations' table does not exist yet")
                print("  (This is normal if the backend hasn't started yet)")

        conn.close()
        print("\n[SUCCESS] All tests passed!")
        return True

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Connection failed!")
        print(f"  {str(e)}")

        # Provide helpful hints
        if "password authentication failed" in str(e):
            print("\n[HINT] Password authentication failed. Possible causes:")
            print("  1. Password in .env doesn't match postgres container")
            print("  2. Postgres container was started with different credentials")
            print("  3. Need to recreate the postgres container with new credentials")
            print("\n  Try: docker-compose down -v && docker-compose up -d postgres")
            print("  (Warning: -v will delete all data in the database)")
        elif "Connection refused" in str(e) or "could not connect" in str(e):
            print("\n[HINT] Cannot connect to database. Possible causes:")
            print("  1. Postgres container is not running")
            print("  2. Port 5432 is not exposed or is blocked")
            print("  3. Connecting from wrong host (use 'localhost' not 'postgres' from host)")
            print("\n  Try: docker-compose ps")

        return False

    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # Check if connection string provided
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
    else:
        # Try to read from .env file
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_file):
            print(f"[*] Reading DATABASE_URL from .env file...")
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        connection_string = line.split('=', 1)[1].strip()
                        # Replace 'postgres' hostname with 'localhost' when testing from host
                        connection_string = connection_string.replace('@postgres:', '@localhost:')
                        break
                else:
                    print("[ERROR] DATABASE_URL not found in .env file")
                    sys.exit(1)
        else:
            print("Usage: python test_db_connection.py [connection_string]")
            print("\nExample:")
            print("  python test_db_connection.py 'postgresql://user:pass@localhost:5432/dbname'")
            print("\nOr create a .env file with DATABASE_URL")
            sys.exit(1)

    success = test_connection(connection_string)
    sys.exit(0 if success else 1)
