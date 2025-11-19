"""
Generation Storage Service - Handles database storage for generation metadata
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    from psycopg2.pool import ThreadedConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available - database storage will not work")


class GenerationStorageService:
    """
    Service for storing and retrieving generation metadata from PostgreSQL database
    
    Handles CRUD operations for generations table and integrates with clip storage.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize generation storage service
        
        Args:
            database_url: PostgreSQL connection URL. If None, reads from DATABASE_URL env var
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for database storage. Install with: pip install psycopg2-binary")
        
        self.database_url = database_url
        if not self.database_url:
            import os
            self.database_url = os.getenv('DATABASE_URL')
            if not self.database_url:
                raise ValueError("DATABASE_URL environment variable must be set")
        
        # Parse database URL to extract connection parameters
        parsed = urlparse(self.database_url)
        self.db_config = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
        
        # Connection pool (lazy initialization)
        self._connection_pool: Optional[ThreadedConnectionPool] = None
        
        # Ensure tables exist on first connection
        self._ensure_tables_exist()
        
        logger.info("GenerationStorageService initialized")
    
    @property
    def connection_pool(self) -> ThreadedConnectionPool:
        """Lazy-loaded connection pool"""
        if self._connection_pool is None:
            self._connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                **self.db_config
            )
        return self._connection_pool
    
    def _get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()
    
    def _put_connection(self, conn):
        """Return a connection to the pool"""
        self.connection_pool.putconn(conn)
    
    def _ensure_tables_exist(self):
        """Create database tables if they don't exist"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            with conn.cursor() as cursor:
                # Create generations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS generations (
                        id VARCHAR(255) PRIMARY KEY,
                        status VARCHAR(50) DEFAULT 'queued',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        metadata JSONB,
                        prompt TEXT,
                        thumbnail_url TEXT,
                        duration_seconds INTEGER
                    );
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generations_status 
                    ON generations(status);
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_generations_created_at 
                    ON generations(created_at DESC);
                """)
                
                conn.commit()
                logger.info("Database tables verified/created")
        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def create_generation(
        self,
        generation_id: str,
        prompt: str,
        status: str = "queued",
        metadata: Optional[Dict[str, Any]] = None,
        duration_seconds: Optional[int] = None
    ) -> bool:
        """
        Create a new generation record in the database
        
        Args:
            generation_id: Unique generation ID
            prompt: User prompt text
            status: Generation status (default: "queued")
            metadata: Optional metadata dictionary (stored as JSONB)
            duration_seconds: Video duration in seconds
        
        Returns:
            True if created successfully, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO generations (id, status, prompt, metadata, duration_seconds, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        prompt = EXCLUDED.prompt,
                        metadata = EXCLUDED.metadata,
                        duration_seconds = EXCLUDED.duration_seconds,
                        updated_at = NOW()
                """, (
                    generation_id,
                    status,
                    prompt,
                    json.dumps(metadata) if metadata else None,
                    duration_seconds
                ))
                conn.commit()
                logger.info(f"Created generation record: {generation_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to create generation: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._put_connection(conn)
    
    def update_generation(
        self,
        generation_id: str,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        thumbnail_url: Optional[str] = None
    ) -> bool:
        """
        Update an existing generation record
        
        Args:
            generation_id: Generation ID to update
            status: New status (optional)
            metadata: Updated metadata (optional, merged with existing)
            thumbnail_url: Thumbnail URL (optional)
        
        Returns:
            True if updated successfully, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                # Build update query dynamically
                updates = []
                params = []
                
                if status is not None:
                    updates.append("status = %s")
                    params.append(status)
                
                if thumbnail_url is not None:
                    updates.append("thumbnail_url = %s")
                    params.append(thumbnail_url)
                
                if metadata is not None:
                    # Merge with existing metadata
                    cursor.execute("SELECT metadata FROM generations WHERE id = %s", (generation_id,))
                    result = cursor.fetchone()
                    existing_metadata = result[0] if result and result[0] else {}
                    
                    if isinstance(existing_metadata, str):
                        existing_metadata = json.loads(existing_metadata)
                    
                    merged_metadata = {**existing_metadata, **metadata}
                    updates.append("metadata = %s")
                    params.append(json.dumps(merged_metadata))
                
                if updates:
                    updates.append("updated_at = NOW()")
                    params.append(generation_id)
                    
                    query = f"""
                        UPDATE generations
                        SET {', '.join(updates)}
                        WHERE id = %s
                    """
                    cursor.execute(query, params)
                    conn.commit()
                    logger.info(f"Updated generation: {generation_id}")
                    return True
                else:
                    logger.warning(f"No updates provided for generation: {generation_id}")
                    return False
        except Exception as e:
            logger.error(f"Failed to update generation: {str(e)}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                self._put_connection(conn)
    
    def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a generation record by ID
        
        Args:
            generation_id: Generation ID to retrieve
        
        Returns:
            Generation record as dictionary, or None if not found
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, status, prompt, thumbnail_url, duration_seconds,
                           metadata, created_at, updated_at
                    FROM generations
                    WHERE id = %s
                """, (generation_id,))
                
                result = cursor.fetchone()
                if result:
                    record = dict(result)
                    # Parse JSONB metadata
                    if record.get('metadata') and isinstance(record['metadata'], str):
                        record['metadata'] = json.loads(record['metadata'])
                    return record
                return None
        except Exception as e:
            logger.error(f"Failed to get generation: {str(e)}")
            return None
        finally:
            if conn:
                self._put_connection(conn)
    
    def list_generations(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List generations with pagination
        
        Args:
            limit: Maximum number of results to return
            offset: Number of results to skip
            status: Optional status filter
        
        Returns:
            List of generation records
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, status, prompt, thumbnail_url, duration_seconds,
                           created_at, updated_at
                    FROM generations
                """
                params = []
                
                if status:
                    query += " WHERE status = %s"
                    params.append(status)
                
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                generations = []
                for row in results:
                    record = dict(row)
                    # Ensure duration_seconds is an integer
                    if record.get('duration_seconds'):
                        record['duration_seconds'] = int(record['duration_seconds'])
                    generations.append(record)
                
                return generations
        except Exception as e:
            logger.error(f"Failed to list generations: {str(e)}")
            return []
        finally:
            if conn:
                self._put_connection(conn)
    
    def count_generations(self, status: Optional[str] = None) -> int:
        """
        Count total number of generations (optionally filtered by status)
        
        Args:
            status: Optional status filter
        
        Returns:
            Total count of generations
        """
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                if status:
                    cursor.execute("SELECT COUNT(*) FROM generations WHERE status = %s", (status,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM generations")
                
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Failed to count generations: {str(e)}")
            return 0
        finally:
            if conn:
                self._put_connection(conn)

