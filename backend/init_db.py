#!/usr/bin/env python3
"""
Database initialization script.
Reads and executes the PostgreSQL init.sql file to create the database schema.

Usage:
    python init_db.py

Or from within the backend container:
    python /app/init_db.py
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql


def get_database_url():
    """Get database URL from environment variable."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    return db_url


def read_init_sql():
    """Read the init.sql file."""
    # Try multiple possible locations
    possible_paths = [
        Path(__file__).parent.parent / "docker" / "postgres" / "init.sql",
        Path("/app/docker/postgres/init.sql"),
        Path("/docker/postgres/init.sql"),
    ]

    for path in possible_paths:
        if path.exists():
            print(f"Found init.sql at: {path}")
            return path.read_text()

    print("ERROR: Could not find init.sql file")
    print(f"Searched in: {[str(p) for p in possible_paths]}")
    sys.exit(1)


def main():
    print("=" * 60)
    print("Database Initialization Script")
    print("=" * 60)

    # Get database connection
    db_url = get_database_url()
    print(f"Connecting to database...")

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cursor = conn.cursor()

        # Check if schema already exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('generation_jobs', 'clips', 'compositions');
        """)
        existing_tables = cursor.fetchone()[0]

        if existing_tables > 0:
            print(f"\n⚠️  WARNING: Found {existing_tables} existing tables")
            response = input("Do you want to continue and potentially overwrite? (yes/no): ")
            if response.lower() != 'yes':
                print("Aborted.")
                sys.exit(0)

        # Read and execute init.sql
        init_sql = read_init_sql()
        print(f"\nExecuting init.sql script...")
        print(f"Script length: {len(init_sql)} characters")

        cursor.execute(init_sql)
        conn.commit()

        # Verify tables were created
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        print(f"\n✅ SUCCESS! Created {len(tables)} tables:")
        for table in tables:
            print(f"   - {table[0]}")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("Database initialization complete!")
        print("=" * 60)

    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
