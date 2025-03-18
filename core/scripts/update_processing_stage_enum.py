# scripts/update_processing_stage_enum.py
import psycopg2
from dotenv import load_dotenv
import os

def update_processing_stage_enum():
    """Update the processing_stage enum type in the database."""
    # Load environment variables
    load_dotenv()
    
    # Connect to the database
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        database=os.getenv("PG_DATABASE", "postgres")
    )
    
    # Set autocommit mode
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Create a new enum type with the updated values
        cursor.execute("""
        CREATE TYPE processing_stage_new AS ENUM (
          'created',
          'captured',
          'contextualizing',
          'contextualized',
          'clarifying',
          'clarified',
          'categorizing',
          'categorized',
          'crystallizing',
          'crystallized',
          'connecting',
          'connected',
          'error'
        );
        """)
        
        # Update tables to use the new enum type
        # First, add a temporary column with the new type
        cursor.execute("""
        ALTER TABLE document_states 
        ADD COLUMN current_stage_new processing_stage_new;
        """)
        
        cursor.execute("""
        ALTER TABLE document_states 
        ADD COLUMN previous_stage_new processing_stage_new;
        """)
        
        # Convert values from old enum to new enum
        # This handles the rename from 'initial' to 'created'
        cursor.execute("""
        UPDATE document_states
        SET current_stage_new = 
            CASE 
                WHEN current_stage::text = 'initial' THEN 'created'::processing_stage_new
                ELSE current_stage::text::processing_stage_new
            END;
        """)
        
        cursor.execute("""
        UPDATE document_states
        SET previous_stage_new = 
            CASE 
                WHEN previous_stage::text = 'initial' THEN 'created'::processing_stage_new
                ELSE previous_stage::text::processing_stage_new
            END
        WHERE previous_stage IS NOT NULL;
        """)
        
        # Update state_transitions table
        cursor.execute("""
        ALTER TABLE state_transitions 
        ADD COLUMN from_stage_new processing_stage_new;
        """)
        
        cursor.execute("""
        ALTER TABLE state_transitions 
        ADD COLUMN to_stage_new processing_stage_new;
        """)
        
        cursor.execute("""
        UPDATE state_transitions
        SET from_stage_new = 
            CASE 
                WHEN from_stage::text = 'initial' THEN 'created'::processing_stage_new
                ELSE from_stage::text::processing_stage_new
            END;
        """)
        
        cursor.execute("""
        UPDATE state_transitions
        SET to_stage_new = 
            CASE 
                WHEN to_stage::text = 'initial' THEN 'created'::processing_stage_new
                ELSE to_stage::text::processing_stage_new
            END;
        """)
        
        # Drop the old columns and rename the new ones
        cursor.execute("""
        ALTER TABLE document_states 
        DROP COLUMN current_stage,
        DROP COLUMN previous_stage,
        RENAME COLUMN current_stage_new TO current_stage,
        RENAME COLUMN previous_stage_new TO previous_stage;
        """)
        
        cursor.execute("""
        ALTER TABLE state_transitions 
        DROP COLUMN from_stage,
        DROP COLUMN to_stage,
        RENAME COLUMN from_stage_new TO from_stage,
        RENAME COLUMN to_stage_new TO to_stage;
        """)
        
        # Drop the old enum type and rename the new one
        cursor.execute("""
        DROP TYPE processing_stage;
        """)
        
        cursor.execute("""
        ALTER TYPE processing_stage_new RENAME TO processing_stage;
        """)
        
        print("Successfully updated processing_stage enum")
        
    except Exception as e:
        print(f"Error updating processing_stage enum: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_processing_stage_enum()