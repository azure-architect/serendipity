# Metacranium Supabase Setup Documentation

## 1. Overview

The Metacranium system uses Supabase with PostgreSQL and pgvector extension as its database backend. This document outlines the setup and configuration process for creating the database infrastructure necessary to support the document processing pipeline.

## 2. Prerequisites

Before setting up the Supabase infrastructure, ensure the following prerequisites are met:

- PostgreSQL 15 or higher
- pgvector extension v0.5.1 or higher
- Docker and Docker Compose
- Supabase CLI (optional, for local development)

## 3. Supabase Container Setup

### 3.1 Docker Compose Configuration

The following docker-compose.yml file configures the Supabase stack with pgvector support:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15.1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    command: ["postgres", "-c", "shared_preload_libraries=pg_stat_statements"]

  pgvector_setup:
    build:
      context: .
      dockerfile: Dockerfile.pgvector
    depends_on:
      - postgres
    volumes:
      - ./migrations:/migrations
    command: >
      bash -c "
        sleep 10 &&
        psql -h postgres -U postgres -d postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;' &&
        psql -h postgres -U postgres -d postgres -f /migrations/01_initial_schema.sql
      "
    environment:
      PGPASSWORD: postgres

volumes:
  pg_data:
```

### 3.2 Custom Dockerfile for pgvector

Create a Dockerfile.pgvector to build a container with pgvector support:

```dockerfile
FROM postgres:15.1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-15 \
    llvm clang \
    && rm -rf /var/lib/apt/lists/*

# Clone and build pgvector
RUN cd /tmp \
    && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install
```

### 3.3 Environment Variables

Create a .env file with the necessary environment variables:

```
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=postgres
```

## 4. Database Schema Setup

### 4.1 Initial Schema Migration

Create the initial schema migration in `migrations/01_initial_schema.sql`:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enum for processing stages
CREATE TYPE processing_stage AS ENUM (
  'created',
  'captured',
  'contextualized',
  'clarified',
  'categorized',
  'crystallized',
  'connected',
  'error'
);

-- Create document_states table
CREATE TABLE IF NOT EXISTS document_states (
  document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  current_stage processing_stage NOT NULL DEFAULT 'created',
  previous_stage processing_stage,
  metadata JSONB DEFAULT '{}',
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  error_info JSONB,
  content_hash TEXT,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  embedding vector(1536),
  embedding_model TEXT,
  embedding_dimension INTEGER,
  embedding_updated_at TIMESTAMP WITH TIME ZONE
);

-- Create state_transitions table
CREATE TABLE IF NOT EXISTS state_transitions (
  transition_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  from_stage processing_stage NOT NULL,
  to_stage processing_stage NOT NULL,
  agent_id TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  message TEXT
);

-- Create state_locks table
CREATE TABLE IF NOT EXISTS state_locks (
  lock_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  locked_by TEXT NOT NULL,
  acquired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create content_metadata table
CREATE TABLE IF NOT EXISTS content_metadata (
  metadata_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  raw_content TEXT NOT NULL,
  source_type TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  creator TEXT,
  input_format TEXT
);

-- Create contextualization_data table
CREATE TABLE IF NOT EXISTS contextualization_data (
  context_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  document_type TEXT,
  topics TEXT[] DEFAULT '{}',
  entities TEXT[] DEFAULT '{}',
  related_domains TEXT[] DEFAULT '{}',
  context_notes TEXT
);

-- Create clarification_data table
CREATE TABLE IF NOT EXISTS clarification_data (
  clarification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  summary TEXT,
  key_points TEXT[] DEFAULT '{}',
  questions_addressed TEXT[] DEFAULT '{}',
  ambiguities_resolved TEXT[] DEFAULT '{}',
  structured_representation JSONB
);

-- Create crystallization_data table
CREATE TABLE IF NOT EXISTS crystallization_data (
  crystal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  insights TEXT[] DEFAULT '{}',
  action_items TEXT[] DEFAULT '{}',
  implications TEXT[] DEFAULT '{}',
  potential_applications TEXT[] DEFAULT '{}',
  value_assessment TEXT
);

-- Create fragment_embeddings table
CREATE TABLE IF NOT EXISTS fragment_embeddings (
  fragment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  fragment TEXT NOT NULL,
  fragment_embedding vector(1536) NOT NULL
);

-- Create connection_map_entries table
CREATE TABLE IF NOT EXISTS connection_map_entries (
  connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  target_id UUID NOT NULL,
  relationship TEXT NOT NULL,
  strength FLOAT NOT NULL,
  connection_type TEXT,
  bidirectional BOOLEAN DEFAULT FALSE,
  discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  discovered_by TEXT,
  context TEXT,
  confidence FLOAT DEFAULT 1.0,
  tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}'
);

-- Create agent_access table
CREATE TABLE IF NOT EXISTS agent_access (
  access_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  stage processing_stage NOT NULL,
  read_access TEXT[] DEFAULT '{}',
  write_access TEXT[] DEFAULT '{}'
);

-- Create processed_documents table
CREATE TABLE IF NOT EXISTS processed_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  original_filename TEXT,
  original_path TEXT,
  processing_stage TEXT NOT NULL,
  processing_history JSONB[] DEFAULT '{}',
  content TEXT NOT NULL,
  capture_results TEXT,
  contextualize_results TEXT,
  clarify_results TEXT,
  categorize_results TEXT,
  crystallize_results TEXT,
  connect_results TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS document_states_current_stage_idx ON document_states(current_stage);
CREATE INDEX IF NOT EXISTS state_transitions_document_id_idx ON state_transitions(document_id);
CREATE INDEX IF NOT EXISTS state_locks_document_id_idx ON state_locks(document_id);
CREATE INDEX IF NOT EXISTS content_metadata_document_id_idx ON content_metadata(document_id);

-- Create vector indexes if extension is available
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS document_states_embedding_idx ON document_states USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';
        EXECUTE 'CREATE INDEX IF NOT EXISTS fragment_embeddings_embedding_idx ON fragment_embeddings USING ivfflat (fragment_embedding vector_cosine_ops) WITH (lists = 100)';
    END IF;
END $$;

-- Create similarity search function
CREATE OR REPLACE FUNCTION find_similar_documents(
  query_embedding vector(1536),
  similarity_threshold float,
  max_results int
)
RETURNS TABLE (
  document_id UUID,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.document_id,
    1 - (d.embedding <=> query_embedding) AS similarity
  FROM 
    document_states d
  WHERE 
    d.embedding IS NOT NULL
    AND 1 - (d.embedding <=> query_embedding) > similarity_threshold
  ORDER BY 
    similarity DESC
  LIMIT max_results;
END;
$$;

-- Create schema_migrations tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
  id SERIAL PRIMARY KEY,
  migration_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  content TEXT NOT NULL
);

-- Record this migration
INSERT INTO schema_migrations (migration_id, name, content)
VALUES ('20250317_initial_schema', 'Initial Schema', 'Initial Metacranium schema setup');
```

## 5. Database Connectivity

### 5.1 Python Connection Setup

Use the following code to connect to the Supabase PostgreSQL database:

```python
import os
import psycopg2
from dotenv import load_dotenv

def get_db_connection():
    """Get a connection to the Supabase PostgreSQL database."""
    # Load environment variables
    load_dotenv(verbose=True)
    
    # Get connection parameters
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "postgres")
    pg_database = os.getenv("PG_DATABASE", "postgres")
    
    # Connect to the database
    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        user=pg_user,
        password=pg_password,
        database=pg_database
    )
    
    return conn
```

### 5.2 Connection Testing

Use this script to test the database connection and verify vector support:

```python
def test_connection():
    """Test connection to the Supabase PostgreSQL database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if vector extension is installed
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        has_vector = cursor.fetchone() is not None
        print(f"Vector extension installed: {'Yes' if has_vector else 'No'}")
        
        # List tables
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Test vector operations if extension is available
        if has_vector:
            print("\nTesting vector operations:")
            try:
                # Create test table
                cursor.execute("""
                CREATE TEMPORARY TABLE vector_test (
                  id SERIAL PRIMARY KEY,
                  embedding vector(3)
                )
                """)
                
                # Insert test data
                cursor.execute("""
                INSERT INTO vector_test (embedding) VALUES ('[1,2,3]')
                RETURNING id
                """)
                
                test_id = cursor.fetchone()[0]
                print(f"Inserted test vector with ID: {test_id}")
                
                # Query test data
                cursor.execute("""
                SELECT embedding FROM vector_test WHERE id = %s
                """, (test_id,))
                
                result = cursor.fetchone()
                print(f"Retrieved vector: {result[0]}")
                
                print("Vector operations test successful")
            except Exception as e:
                print(f"Vector operations test failed: {e}")
        
        conn.close()
        print("\nConnection test completed successfully")
        return True
        
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
```

## 6. Backup and Restore

### 6.1 Backup Script

Create a script for backing up the database:

```bash
#!/bin/bash
# backup.sh - Vector-aware backup script

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/metacranium_backup_${TIMESTAMP}.dump"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

# Create a complete backup with all extensions and data
echo "Creating backup at ${BACKUP_FILE}..."
docker exec -it postgres pg_dump -U postgres --format=custom --file=/tmp/backup.dump --verbose

# Copy the backup from the container
docker cp postgres:/tmp/backup.dump $BACKUP_FILE

# Remove temporary backup from container
docker exec -it postgres rm /tmp/backup.dump

echo "Backup completed: ${BACKUP_FILE}"
```

### 6.2 Restore Script

Create a script for restoring from backup:

```bash
#!/bin/bash
# restore.sh - Vector-aware restore script

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Error: Please provide a backup file path"
  echo "Usage: $0 /path/to/backup/file.dump"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_FILE"
  exit 1
fi

# Copy the backup to the container
echo "Copying backup to container..."
docker cp $BACKUP_FILE postgres:/tmp/backup.dump

# Restore the database
echo "Restoring database from backup..."
docker exec -it postgres pg_restore -U postgres --clean --if-exists --no-owner --no-privileges --verbose --dbname=postgres /tmp/backup.dump

# Remove temporary backup from container
docker exec -it postgres rm /tmp/backup.dump

echo "Restore completed"
```

## 7. Migration Management

### 7.1 Python Migration Script

Create a script for managing database migrations:

```python
import os
import uuid
import psycopg2
from dotenv import load_dotenv

def create_migration(name, sql_content):
    """Create and apply a new migration."""
    # Load environment variables
    load_dotenv(verbose=True)
    
    # Get connection parameters
    pg_host = os.getenv("PG_HOST", "localhost")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_user = os.getenv("PG_USER", "postgres")
    pg_password = os.getenv("PG_PASSWORD", "postgres")
    pg_database = os.getenv("PG_DATABASE", "postgres")
    
    # Generate migration ID
    migration_id = f"{name}_{uuid.uuid4().hex[:8]}"
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            user=pg_user,
            password=pg_password,
            database=pg_database
        )
        
        # Set autocommit mode
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if schema_migrations table exists
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'schema_migrations'
        )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        # Create schema_migrations table if it doesn't exist
        if not table_exists:
            cursor.execute("""
            CREATE TABLE schema_migrations (
              id SERIAL PRIMARY KEY,
              migration_id TEXT UNIQUE NOT NULL,
              name TEXT NOT NULL,
              applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
              content TEXT NOT NULL
            )
            """)
        
        # Check if migration has already been applied
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM schema_migrations 
            WHERE migration_id = %s
        )
        """, (migration_id,))
        
        migration_exists = cursor.fetchone()[0]
        
        if migration_exists:
            print(f"Migration {migration_id} has already been applied")
            return False
        
        # Apply the migration
        print(f"Applying migration {migration_id}...")
        cursor.execute(sql_content)
        
        # Record the migration
        cursor.execute("""
        INSERT INTO schema_migrations (migration_id, name, content)
        VALUES (%s, %s, %s)
        """, (migration_id, name, sql_content))
        
        conn.close()
        print(f"Migration {migration_id} applied successfully")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
```

## 8. Testing and Verification

### 8.1 Vector Operations Test

Create a test script to verify vector operations:

```python
def test_vector_operations():
    """Test vector operations in the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test document insertion with embedding
        print("Testing document insertion with embedding...")
        
        # Create a test document with embedding
        import numpy as np
        test_embedding = np.random.rand(1536).tolist()
        embedding_str = "[" + ",".join(str(x) for x in test_embedding) + "]"
        
        cursor.execute("""
        INSERT INTO document_states 
            (current_stage, metadata, embedding, embedding_model, embedding_dimension) 
        VALUES 
            ('created', '{"test": true}', %s::vector, 'test-model', 1536) 
        RETURNING document_id
        """, (embedding_str,))
        
        doc_id = cursor.fetchone()[0]
        print(f"Created test document with ID: {doc_id}")
        
        # Test similarity search
        print("Testing similarity search...")
        
        # Generate a query embedding
        query_embedding = np.random.rand(1536).tolist()
        query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        cursor.execute("""
        SELECT document_id, 1 - (embedding <=> %s::vector) AS similarity
        FROM document_states
        WHERE embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT 5
        """, (query_embedding_str,))
        
        results = cursor.fetchall()
        print(f"Found {len(results)} similar documents")
        for result in results:
            print(f"Document ID: {result[0]}, Similarity: {result[1]}")
        
        # Clean up test data
        cursor.execute("""
        DELETE FROM document_states WHERE document_id = %s
        """, (doc_id,))
        
        conn.commit()
        conn.close()
        print("Vector operations test completed successfully")
        return True
        
    except Exception as e:
        print(f"Vector operations test failed: {e}")
        return False
```

### 8.2 State Transition Test

Create a test script to verify document state transitions:

```python
def test_state_transitions():
    """Test document state transitions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create a test document
        cursor.execute("""
        INSERT INTO document_states (current_stage, metadata)
        VALUES ('created', '{"test": true}')
        RETURNING document_id
        """)
        
        doc_id = cursor.fetchone()[0]
        print(f"Created test document with ID: {doc_id}")
        
        # Test state transitions through the pipeline
        stages = [
            "created",
            "captured",
            "contextualized",
            "clarified",
            "categorized",
            "crystallized",
            "connected"
        ]
        
        for i in range(len(stages) - 1):
            from_stage = stages[i]
            to_stage = stages[i + 1]
            
            # Record transition
            cursor.execute("""
            INSERT INTO state_transitions 
                (document_id, from_stage, to_stage, agent_id, message)
            VALUES
                (%s, %s, %s, 'test-agent', %s)
            RETURNING transition_id
            """, (doc_id, from_stage, to_stage, f"Test transition from {from_stage} to {to_stage}"))
            
            transition_id = cursor.fetchone()[0]
            
            # Update document state
            cursor.execute("""
            UPDATE document_states
            SET current_stage = %s, previous_stage = %s
            WHERE document_id = %s
            """, (to_stage, from_stage, doc_id))
            
            print(f"Transitioned document from {from_stage} to {to_stage} (ID: {transition_id})")
        
        # Verify final state
        cursor.execute("""
        SELECT current_stage, previous_stage
        FROM document_states
        WHERE document_id = %s
        """, (doc_id,))
        
        result = cursor.fetchone()
        print(f"Final document state: Current = {result[0]}, Previous = {result[1]}")
        
        # Clean up test data
        cursor.execute("""
        DELETE FROM state_transitions WHERE document_id = %s
        """, (doc_id,))
        
        cursor.execute("""
        DELETE FROM document_states WHERE document_id = %s
        """, (doc_id,))
        
        conn.commit()
        conn.close()
        print("State transition test completed successfully")
        return True
        
    except Exception as e:
        print(f"State transition test failed: {e}")
        return False
```

## 9. Deployment Instructions

### 9.1 Local Development Setup

To set up the Metacranium database for local development:

1. Clone the repository
2. Navigate to the project directory
3. Create the necessary configuration files:
   - docker-compose.yml
   - Dockerfile.pgvector
   - .env
4. Initialize the database:
   ```bash
   docker-compose up -d
   ```
5. Verify the setup:
   ```bash
   python -c "from db_utils import test_connection; test_connection()"
   ```

### 9.2 Production Deployment

For production deployment on the server at 192.168.0.120:

1. SSH into the server
2. Navigate to the deployment directory:
   ```bash
   cd /opt/metacranium
   ```
3. Pull the latest configuration files
4. Update environment variables:
   ```bash
   cp .env.example .env
   vi .env  # Edit with production values
   ```
5. Start the containers:
   ```bash
   docker-compose up -d
   ```
6. Apply migrations:
   ```bash
   python scripts/apply_migrations.py
   ```
7. Verify the deployment:
   ```bash
   python scripts/test_deployment.py
   ```

## 10. Troubleshooting

### 10.1 Connection Issues

If you encounter connection issues:

1. Verify the environment variables:
   ```bash
   cat .env
   ```

2. Check the container status:
   ```bash
   docker-compose ps
   ```

3. Check the container logs:
   ```bash
   docker-compose logs postgres
   ```

### 10.2 Vector Extension Issues

If pgvector isn't working properly:

1. Check if the extension is installed:
   ```bash
   docker exec -it postgres psql -U postgres -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

2. Try reinstalling the extension:
   ```bash
   docker exec -it postgres bash -c "cd /tmp && 
   git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git && 
   cd pgvector && make && make install"
   
   docker exec -it postgres psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

3. Verify the installation:
   ```bash
   docker exec -it postgres psql -U postgres -c "CREATE TEMPORARY TABLE vector_test (v vector(3)); INSERT INTO vector_test VALUES ('[1,2,3]'); SELECT * FROM vector_test;"
   ```

## 11. Conclusion

This document provides comprehensive instructions for setting up the Supabase PostgreSQL database with pgvector support for the Metacranium system. By following these steps, you can create a robust database infrastructure that supports the sophisticated document processing pipeline with vector embedding capabilities.

The setup includes:
- PostgreSQL with pgvector extension for vector operations
- Complete schema for document processing pipeline
- Backup and restore functionality
- Migration management system
- Testing and verification tools
- Deployment instructions for both development and production

This infrastructure forms the foundation of the Metacranium system, enabling sophisticated document processing with semantic search and relationship discovery capabilities.