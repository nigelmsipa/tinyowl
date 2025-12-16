sdf# TinyOwl 🦉

A personal knowledge AI system that starts with RAG (Retrieval-Augmented Generation) and evolves to fine-tuning TinyLlama on a curated library of essential books. 

## Project Vision

TinyOwl aims to build a personal AI assistant trained on books considered essential in various domains. The project starts with theology texts (KJV Bible + 5 Conflict of Ages books), and will expand to include programming, homesteading, history, and other domains of interest.

The core pipeline follows this progression:
1. **PDF Ingestion**: Extract and clean text from source PDFs
2. **Vector Database**: Store text chunks with embeddings for efficient retrieval
3. **RAG Testing**: Test retrieval quality with domain-specific questions
4. **Q&A Generation**: Generate high-quality question-answer pairs
5. **Fine-tuning**: Train TinyLlama on the curated knowledge

## Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/tinyowl.git
cd tinyowl

# Install dependencies
pip install -r requirements.txt

# Prepare your domain data
# Place PDFs in domains/theology/raw/

# Run ingestion
python scripts/ingest.py --config configs/sources.yaml

# Start the chat interface (CLI)
python -m chat_app.main
```

## Project Structure

```
tinyowl/
├── domains/               # Knowledge domains
│   └── theology/          # First domain: theology
│       ├── raw/           # Original PDFs
│       ├── processed/     # Cleaned text + metadata
│       └── chunks/        # Final chunked data
├── vectordb/             # ChromaDB persistent storage
├── scripts/              # Processing scripts
├── configs/              # Configuration files
├── tests/                # Validation tests
└── docs/                 # Documentation
```

## Key Principles

- **Clean, reproducible pipeline**: Consistent processing from raw data to model training
- **Domain-aware but cross-searchable**: Organize by domain but enable cross-domain queries
- **Quality over speed**: Focus on high-quality data processing and retrieval
- **Git-ready**: Version control friendly (large files excluded)
- **Expandable**: Easily add new knowledge domains
- **Provenance tracking**: Maintain source information for all training data

## Roadmap

1. **MVP (Current)**: RAG system with theology domain
   - PDF ingestion pipeline
   - Basic RAG chat interface
   - Retrieval validation

2. **Enhancement**: Improve data processing
   - Better chunking strategies
   - Advanced metadata extraction
   - Cross-references between sources

3. **Expansion**: Add new domains
   - Programming books/documentation
   - Homesteading guides
   - Historical texts

4. **Training Data**: Generate fine-tuning datasets
   - Create Q&A pairs based on content
   - Synthetic task generation

5. **Fine-tuning**: Train custom models
   - Fine-tune TinyLlama on curated corpus
   - Evaluate and iterate

## Contributing

This is a personal project, but suggestions and ideas are welcome.

## License

Personal use only. All content rights belong to their respective owners.

## Chat CLI + Ollama

- Launch: `python -m chat_app.main`
- Quick model switch: `/model` (interactive picker with ↑/↓ + Enter) or `/ai model <name|#|partial>`
- AI commands:
  - `/ai status` — show AI toggle, Ollama availability, and model
  - `/ai on` | `/ai off` | `/ai toggle` — control enhancement
  - `/ai models` — list installed Ollama models (numbered)
  - `/ai default [name]` — save default model and enabled flag for future sessions
- Env overrides:
  - `TINYOWL_OLLAMA_HOST` (default `http://localhost:11434`)
  - `TINYOWL_OLLAMA_MODEL` (default `mistral:latest`)
- Behavior:
  - If Ollama is unavailable, chat features still work; AI enhancements are skipped gracefully.
