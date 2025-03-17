# Metacranium Embedding Strategy Documentation

## 1. Overview

The Metacranium system employs a sophisticated embedding strategy to transform documents and their fragments into vector representations that enable semantic search, similarity matching, and relationship discovery. This strategy is fundamental to the system's ability to create connections between documents based on meaning rather than just keywords.

## 2. Embedding Models

### 2.1 Primary Embedding Model

```python
# Current production embedding model
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text:latest"
DEFAULT_EMBEDDING_DIMENSIONS = 768
```

The system uses `nomic-embed-text:latest` as the primary embedding model, which generates 768-dimensional vectors. This model is accessed through Ollama for local processing, providing:

- Privacy by keeping data local
- Speed through local processing
- Consistency across all system components

### 2.2 Embedding Generation

```python
def get_embedding(text: str) -> List[float]:
    """Generate embedding using local Ollama instance"""
    import ollama
    client = ollama.Client()
    response = client.embeddings(model="nomic-embed-text:latest", prompt=text)
    return response['embedding']
```

The embeddings are generated via Ollama's client library rather than its API, allowing for direct integration without network overhead.

### 2.3 Model Flexibility

The schema supports multiple embedding models through metadata fields:

```sql
embedding_model TEXT,
embedding_dimension INTEGER,
embedding_updated_at TIMESTAMP WITH TIME ZONE
```

This allows for:
- Tracking which model generated each embedding
- Supporting different dimensions for different models
- Recording when embeddings were last updated

## 3. Embedding Targets

### 3.1 Document-Level Embeddings

Each document has a full-document embedding stored in the `document_states` table:

```sql
embedding vector(1536)
```

While the current model produces 768-dimensional vectors, the schema supports 1,536 dimensions to:
- Allow for future model upgrades
- Support larger models when necessary
- Maintain compatibility with various embedding technologies

### 3.2 Fragment-Level Embeddings

Documents are also broken into meaningful fragments, each with its own embedding:

```sql
CREATE TABLE fragment_embeddings (
  fragment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  document_id UUID REFERENCES document_states(document_id),
  fragment TEXT NOT NULL,
  fragment_embedding vector(1536) NOT NULL
);
```

This enables:
- More granular semantic search
- Identification of relationships between specific parts of documents
- Better precision in similarity matching

### 3.3 Connection Map Embeddings

Relationship mappings between documents are also embedded:

```python
class ConnectionMapEntry(VectorizedModel):
    """Represents a connection to another document."""
    target_id: UUID
    relationship: str
    strength: float
    # ... other fields ...
    # Inherits embedding from VectorizedModel
```

By embedding the connections themselves, the system can:
- Discover meta-patterns in relationships
- Group similar types of connections
- Enable search across relationship types

## 4. Embedding Storage and Indexing

### 4.1 PGVector Storage

Embeddings are stored using PostgreSQL's pgvector extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

This provides:
- Native vector operations within the database
- Efficient vector similarity calculations
- Integration with PostgreSQL's robust query capabilities

### 4.2 Vector Indexing

Optimized indexes are created for vector operations:

```sql
CREATE INDEX document_states_embedding_idx 
ON document_states 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);
```

These indexes use the IVFFlat algorithm, which:
- Divides the vector space into clusters
- Enables approximate nearest neighbor search
- Dramatically improves query performance on large datasets

### 4.3 JSONB Fallback

For environments without pgvector support, a fallback mechanism stores embeddings as JSONB:

```sql
ALTER TABLE document_states ADD COLUMN IF NOT EXISTS embedding_json JSONB;
```

While this doesn't support native vector operations, it:
- Preserves the embedding data
- Enables transferring data between environments
- Maintains compatibility with non-vector-enabled PostgreSQL instances

## 5. Vector Operations

### 5.1 Similarity Search

The system provides functions for similarity searches:

```sql
CREATE FUNCTION find_similar_documents(
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
```

This function:
- Calculates cosine distance between vectors
- Converts distance to similarity (1 - distance)
- Filters results by a configurable threshold
- Limits results to a manageable number

### 5.2 Clustering

Vector embeddings enable document clustering operations:

```python
def cluster_documents(document_ids: List[UUID], n_clusters: int = 5):
    """Group documents into clusters based on vector similarity"""
    # Fetch embeddings for documents
    embeddings = fetch_document_embeddings(document_ids)
    
    # Use scikit-learn for clustering
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=n_clusters)
    clusters = kmeans.fit_predict(embeddings)
    
    # Return document_id to cluster mapping
    return dict(zip(document_ids, clusters))
```

This supports:
- Automatic document organization
- Topic discovery across document sets
- Identification of outlier documents

### 5.3 Dimensionality Reduction

For visualization and analysis, embeddings can be reduced to lower dimensions:

```python
def reduce_dimensions(embeddings: List[List[float]], dimensions: int = 2):
    """Reduce embedding dimensions for visualization"""
    from sklearn.manifold import TSNE
    reduced = TSNE(n_components=dimensions).fit_transform(embeddings)
    return reduced
```

This enables:
- Document map visualization
- Relationship exploration in 2D/3D space
- Intuitive navigation of the document space

## 6. Embedding Generation Pipeline

### 6.1 Document Processing Flow

```
Raw Document → Text Extraction → Text Chunking → Embedding Generation → Database Storage
```

Each step is handled by specialized components:

1. **Text Extraction**: Converts various formats to plain text
2. **Text Chunking**: Divides text into meaningful fragments
3. **Embedding Generation**: Creates vectors for documents and fragments
4. **Database Storage**: Persists vectors with metadata

### 6.2 Embedding Refresh Strategy

Embeddings can be refreshed when:
- A model upgrade occurs
- Document content changes
- Processing stage transitions happen

The refresh process:
1. Identifies documents needing updates
2. Generates new embeddings
3. Updates database records
4. Updates the `embedding_updated_at` timestamp

## 7. Performance Considerations

### 7.1 Batch Processing

For efficiency, embeddings are typically processed in batches:

```python
def batch_embed_documents(document_ids: List[UUID], batch_size: int = 10):
    """Generate embeddings for multiple documents in batches"""
    results = []
    
    for i in range(0, len(document_ids), batch_size):
        batch = document_ids[i:i+batch_size]
        texts = fetch_document_texts(batch)
        
        # Process batch with Ollama
        embeddings = []
        for text in texts:
            embedding = get_embedding(text)
            embeddings.append(embedding)
        
        # Store batch results
        update_document_embeddings(batch, embeddings)
        results.extend(zip(batch, embeddings))
    
    return results
```

This approach:
- Reduces connection overhead
- Utilizes model caching more effectively
- Enables parallel processing when available

### 7.2 Caching Strategy

To improve performance, embeddings are cached:
- In-memory for active processing sessions
- In database for long-term storage
- With metadata for tracking freshness

### 7.3 Embedding Compression

For very large document sets, optional compression can be applied:

```python
def compress_embedding(embedding: List[float], target_dim: int = 384):
    """Compress embedding to lower dimensionality"""
    # Use PCA for deterministic compression
    from sklearn.decomposition import PCA
    import numpy as np
    
    pca = PCA(n_components=target_dim)
    compressed = pca.fit_transform(np.array(embedding).reshape(1, -1))
    return compressed[0].tolist()
```

This enables:
- Reduced storage requirements
- Faster similarity calculations
- Trade-off between precision and performance

## 8. Conclusion

The Metacranium embedding strategy transforms documents into a rich semantic space where meaning and relationships can be discovered algorithmically. By leveraging local LLM models, pgvector storage, and optimized indexing, the system provides powerful semantic capabilities while maintaining privacy, performance, and extensibility.

This embedding foundation enables the core Metacranium features:
- Semantic document search
- Automatic relationship discovery
- Knowledge clustering and organization
- Serendipitous connection revelation

The strategy is designed to evolve with advancements in embedding models while maintaining backward compatibility with existing data.