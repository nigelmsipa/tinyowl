# TinyOwl Expansion Guide

This document outlines the process for adding new knowledge domains to your TinyOwl personal AI system.

## Adding a New Domain

TinyOwl is designed to grow with your knowledge interests. Follow these steps to add a new domain:

## 1. Domain Planning

### Define Domain Scope
- Determine the specific subject area (e.g., programming, homesteading, history)
- Identify core texts and resources for the domain
- Consider how this domain relates to existing domains

### Source Selection Criteria
- Choose authoritative, comprehensive resources
- Prefer content with clear structure (chapters, sections)
- Consider content quality and relevance to your goals
- Ensure proper licensing/permissions for personal use

## 2. Directory Setup

Create the necessary directory structure:

```bash
# Create domain directories
mkdir -p domains/new_domain_name/{raw,processed,chunks}

# Add placeholder files
touch domains/new_domain_name/raw/.gitkeep
touch domains/new_domain_name/processed/.gitkeep
touch domains/new_domain_name/chunks/.gitkeep
```

## 3. Configuration

### Create Sources Configuration

Create a new YAML file or extend the existing one:

```bash
# Option 1: Create domain-specific config
cp configs/sources.yaml configs/sources_new_domain.yaml
# Edit the new file with your domain's sources

# Option 2: Extend the main config
# Add your new sources to configs/sources.yaml
```

Example configuration for a programming domain:

```yaml
domain: programming
description: "Core programming language references and books"

sources:
  - id: python_docs
    title: "Python Documentation"
    type: documentation
    author: "Python Software Foundation"
    year: 2023
    path: "domains/programming/raw/python_docs.pdf"
    language: "english"
    description: "Official Python language documentation"
    structure:
      has_chapters: true
      has_sections: true
    chunking_strategy: "section"
  
  # Additional sources...
```

### Update Chunking Strategy

Evaluate if the existing chunking strategies work for your new domain. If not, extend `configs/chunking.yaml` with domain-specific strategies:

```yaml
strategies:
  # Add new strategy for code documentation
  code_documentation:
    description: "Chunk by function/class documentation"
    chunk_type: "semantic_unit"
    chunk_unit: "function"
    include_context:
      module: true
      class: true
    metadata_fields:
      - language
      - function_name
      - parameter_list
```

### Configure Models

Update `configs/models.yaml` if your domain requires specific embedding or LLM models.

## 4. Ingestion Process

### Data Preparation
1. Add your source PDFs to `domains/new_domain/raw/`
2. Consider any pre-processing needed (OCR, formatting)

### Run Ingestion
```bash
# Run the ingestion script with your new domain
python scripts/ingest.py --domain new_domain --config configs/sources_new_domain.yaml
```

### Validate Processing
- Check processed outputs in `domains/new_domain/processed/`
- Verify chunk quality in `domains/new_domain/chunks/`
- Examine vector embeddings in ChromaDB

## 5. Testing

### Create Domain Test Questions
Add a new test file:

```bash
# Create test file
touch tests/new_domain_questions.py
```

Add domain-specific test questions:

```python
# Example for programming domain
PROGRAMMING_QUESTIONS = [
    "How does Python's garbage collection work?",
    "What are the differences between Python 2 and Python 3?",
    "Explain Python's list comprehension syntax with examples.",
    # Add more domain-specific questions
]
```

### Run Validation
```bash
python scripts/validate.py --domain new_domain
```

## 6. Cross-Domain Integration

### Update Schema
Ensure your domain metadata is compatible with the existing schema

### Test Cross-Domain Queries
Create tests that span multiple domains to validate cross-domain retrieval

## 7. Performance Optimization

### Collection Management
Consider ChromaDB collection strategies:
- Single collection with domain filters
- Separate collections with cross-collection search

### Embedding Selection
Different domains may benefit from specialized embedding models:
- Code-specific embeddings for programming
- Scientific embeddings for technical domains

## 8. Fine-Tuning Preparation

Once your domain has been validated with the RAG system:

1. Generate domain-specific training examples
2. Create a balanced dataset across all domains
3. Update the fine-tuning pipeline for the new combined dataset

## Best Practices

- **Start small**: Begin with 3-5 core texts before expanding
- **Be consistent**: Use similar processing across domains
- **Document sources**: Keep detailed records of all source materials
- **Version your data**: Tag data with version information
- **Test thoroughly**: Create comprehensive validation questions

## Common Challenges

- **Domain overlap**: Handle concepts that span multiple domains
- **Inconsistent structure**: Adapt chunking for different content types
- **Specialized terminology**: Consider domain-specific embeddings
- **Large volume**: Implement batch processing for large domains

## Domain-Specific Considerations

### Programming
- Code snippets require special handling
- Consider code-specific embeddings
- Structure chunks around functions/methods

### History
- Timeline information is important
- Geographic context may be relevant
- Cross-referencing between events is valuable

### Science/Technical
- Formulas and equations need special handling
- Diagrams and figures are important context
- Technical terminology requires precision

By following this guide, you can systematically expand TinyOwl to encompass all your knowledge domains of interest.
