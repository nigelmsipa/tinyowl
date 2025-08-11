# TinyOwl Pipeline Documentation

This document explains the complete data pipeline for TinyOwl, from raw PDF ingestion to fine-tuning a TinyLlama model on your curated knowledge.

## Overview

```
Raw PDFs → Text Extraction → Cleaning → Chunking → Vectorization → RAG → Q&A Generation → Fine-tuning
```

## 1. Data Ingestion

### PDF Processing
- **Input**: Raw PDFs in `domains/<domain>/raw/`
- **Process**:
  - Extract text using PyPDF
  - Preserve structure (chapters, sections, etc.)
  - Extract metadata (titles, page numbers, etc.)
- **Output**: Cleaned text files in `domains/<domain>/processed/`

### Text Cleaning
- Remove headers/footers/page numbers
- Fix common OCR errors
- Normalize whitespace and special characters
- Split into logical sections
- Generate metadata JSON files

## 2. Chunking

### Strategy Selection
- Different content types require different chunking strategies
- Bible: verse-level chunking with context
- Books: paragraph-level with semantic boundaries
- See `configs/chunking.yaml` for detailed strategies

### Chunk Processing
- **Input**: Processed text from `domains/<domain>/processed/`
- **Process**:
  - Apply domain-specific chunking strategy
  - Generate chunk metadata
  - Ensure chunks have sufficient context
  - Add source attribution
- **Output**: Text chunks in `domains/<domain>/chunks/`

## 3. Vector Database

### Embedding Generation
- **Model**: Sentence Transformers (all-MiniLM-L6-v2)
- Generate embeddings for each text chunk
- Store vectors alongside chunk text and metadata

### ChromaDB Setup
- Persistent storage in `vectordb/`
- Collections per domain
- Metadata filtering capabilities
- Cross-collection search capability

## 4. RAG System

### Query Processing
- Convert user question to vector embedding
- Perform similarity search to retrieve relevant chunks
- Apply metadata filters based on query context

### Response Generation
- Pass retrieved chunks as context to LLM
- Generate response with source citations
- Track retrieval performance metrics

## 5. Validation

### Quality Assessment
- Test suite in `tests/`
- Domain-specific test questions
- Measures retrieval precision and recall
- Identifies knowledge gaps

### Feedback Loop
- Log failed retrievals
- Identify chunking issues
- Update processing strategies based on findings

## 6. Q&A Generation

### Training Data Creation
- **Input**: Successfully retrieved chunks
- **Process**:
  - Generate diverse question types (factual, analytical, comparative)
  - Create ground-truth answers with source citations
  - Review and filter for quality
- **Output**: JSONL files for fine-tuning

## 7. Fine-tuning

### TinyLlama Preparation
- Quantize model for efficiency
- Prepare adapter layers for PEFT (Parameter-Efficient Fine-Tuning)
- Configure training hyperparameters

### Training Process
- LoRA fine-tuning on curated dataset
- Evaluation on held-out validation set
- Iterative improvement

## 8. Deployment

### Model Serving
- Optimize for inference
- API endpoints for query-response
- Hybrid RAG + fine-tuned approach

### Continuous Improvement
- Monitor performance
- Expand knowledge domains
- Update with new content

## File Format Standards

### Source Files
See `configs/sources.yaml` for structure

### Chunk Format
```json
{
  "id": "chunk_unique_id",
  "text": "Actual chunk content...",
  "metadata": {
    "source_id": "reference to sources.yaml",
    "domain": "theology",
    "title": "Original document title",
    "author": "Author name",
    "location": {
      "page": 42,
      "chapter": 5,
      "section": "Section Title"
    },
    "timestamp": "2023-10-15T14:32:00Z"
  }
}
```

### Embeddings Storage
ChromaDB manages vector storage with the above metadata available for filtering.

## Scaling Considerations

- **Vector DB**: ChromaDB scales horizontally as collection grows
- **Processing**: Batch processing for large document sets
- **Fine-tuning**: PEFT techniques reduce memory requirements

## Security and Privacy

- All data remains local
- No cloud dependencies
- Source attribution preserved throughout pipeline
