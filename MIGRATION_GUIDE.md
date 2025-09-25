# TinyOwl Migration Guide
**Transferring TinyOwl to New Machine - Complete Instructions**

## Project Size Analysis
- **Total Project**: 30GB (includes large temp files, multiple venvs)
- **Essential Transfer**: ~4.2GB (git + vectordb + domains)
- **ChromaDB**: 3.3GB (166K+ theological embeddings)
- **Source Data**: 497MB (processed JSON chunks)
- **Git Repository**: 331MB (code + documentation)

## Recommended Migration Strategy

### Method 1: Selective Transfer (FASTEST - 4.2GB)

#### Step 1: Prepare Transfer Package (Current Machine)
```bash
cd /home/nigel/tinyowl

# Create ChromaDB archive (most critical component)
echo "Creating ChromaDB archive..."
tar -czf ../tinyowl-vectordb.tar.gz vectordb/

# Create domains archive (source data for rebuilding if needed)
echo "Creating domains archive..."
tar -czf ../tinyowl-domains.tar.gz domains/

# Create requirements snapshot
pip freeze > requirements-frozen.txt

# Check archive sizes
ls -lh ../tinyowl-*.tar.gz
```

#### Step 2: Transfer Files to New Machine
**Transfer these files** (total ~4.2GB):
- Git repository: `git clone https://github.com/nigelmsipa/tinyowl.git`
- ChromaDB archive: `tinyowl-vectordb.tar.gz` (3.3GB)
- Domains archive: `tinyowl-domains.tar.gz` (497MB)
- Requirements: `requirements-frozen.txt`

#### Step 3: Setup on New Machine
```bash
# Clone repository
git clone https://github.com/nigelmsipa/tinyowl.git
cd tinyowl

# Extract ChromaDB (CRITICAL - contains all embeddings)
tar -xzf ../tinyowl-vectordb.tar.gz

# Extract domains (source data)
tar -xzf ../tinyowl-domains.tar.gz

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements-frozen.txt

# Test installation
python -m chat_app.main
```

### Method 2: Complete Archive (COMPREHENSIVE - 30GB)

#### For Complete Transfer Including All History
```bash
cd /home/nigel

# Create complete project archive (excludes only git and venvs)
tar -czf tinyowl-complete-$(date +%Y%m%d).tar.gz \
    --exclude='tinyowl/.git' \
    --exclude='tinyowl/venv' \
    --exclude='tinyowl/.venv*' \
    --exclude='tinyowl/tmp' \
    tinyowl/

# Transfer the archive + clone git separately for latest updates
```

### Method 3: Rebuild Strategy (MINIMAL - <1GB)

#### For Slow Connections - Transfer Only Code, Rebuild ChromaDB
```bash
# Transfer only:
# - Git repository (clone from GitHub)
# - Source data files (domains/ if preserved)
# - Requirements file

# On new machine - rebuild ChromaDB (2-4 hours):
cd tinyowl
source .venv/bin/activate

# Re-embed all content (if you have domains/ data)
python scripts/generate_embeddings.py --all-collections
python scripts/generate_strongs_embeddings.py
```

## Critical Files Checklist

### ✅ MUST TRANSFER
- **`vectordb/`** - 3.3GB ChromaDB with all embeddings (CRITICAL)
- **`domains/`** - 497MB processed theological data
- **`chat_app/`** - CLI application code
- **`scripts/`** - Processing and embedding scripts
- **`configs/`** - OSIS canonical system and configurations

### ✅ IMPORTANT TO TRANSFER
- **`requirements-frozen.txt`** - Exact dependency versions
- **`README.md`** - Documentation
- **`CLAUDE.md`** - Complete development history
- **`STRATEGIC_DESIGN_IMPROVEMENTS.md`** - Strategic planning

### ⚠️ OPTIONAL (Can Regenerate)
- **`.venv/`** - Virtual environment (rebuild on new machine)
- **`chat-app/`** - Duplicate implementation
- **`backups/`** - Old backup files
- **`vectordb_backup_*/`** - Old backup directories

### ❌ DON'T TRANSFER
- **`venv/`** - Old virtual environments
- **`.venv311/`** - Alternative virtual environments
- **`tmp/`** - Temporary files
- **Large log files** - Can regenerate

## Verification Steps (New Machine)

### Test 1: ChromaDB Integrity
```bash
source .venv/bin/activate
python -c "
import chromadb
client = chromadb.PersistentClient(path='vectordb')
collections = client.list_collections()
print(f'Collections: {len(collections)}')
for c in collections:
    print(f'  {c.name}: {c.count()} chunks')
"
```

**Expected Output**:
```
Collections: 7
  kjv_verses: 31102 chunks
  kjv_pericopes: 9968 chunks
  kjv_chapters: 1189 chunks
  web_verses: 31098 chunks
  web_pericopes: 9967 chunks
  web_chapters: 1189 chunks
  strongs_concordance_entries: 81882 chunks
```

### Test 2: Chat Application
```bash
source .venv/bin/activate
python -m chat_app.main

# Test these commands:
# @aaron (should return 218 verses)
# @strong:175 (should return Hebrew definition)
# &john3:16 (should display verse)
# /stats (should show 166K+ chunks)
```

### Test 3: Embedding Model Access
```bash
# Verify BGE-large model downloads correctly
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-en-v1.5')
print('BGE-large model loaded successfully')
"
```

## Troubleshooting Common Issues

### Issue 1: ChromaDB Version Mismatch
```bash
# If ChromaDB complains about version differences
pip install chromadb==1.1.0  # Match exact version
```

### Issue 2: Missing BGE Model
```bash
# If embeddings fail to load
python -c "
from sentence_transformers import SentenceTransformer
SentenceTransformer('BAAI/bge-large-en-v1.5').save('models/bge-large-en-v1.5')
"
```

### Issue 3: Permission Errors
```bash
# Fix ChromaDB permissions
sudo chown -R $USER:$USER vectordb/
chmod -R 755 vectordb/
```

## Performance Validation

After transfer, verify performance:
- **Query response**: <300ms for @aaron
- **Typeahead**: <100ms for auto-complete
- **AI integration**: Ollama connects if available
- **Memory usage**: <4GB RAM during normal operation

## Backup Strategy for New Machine

Once TinyOwl is running on new machine:
```bash
# Create periodic backups
cd /path/to/tinyowl

# Weekly ChromaDB backup
tar -czf backups/vectordb-backup-$(date +%Y%m%d).tar.gz vectordb/

# Monthly complete backup
tar -czf backups/tinyowl-complete-$(date +%Y%m%d).tar.gz \
    --exclude='.venv*' --exclude='backups/' .
```

## Migration Time Estimates

### Internet Connection Based
- **Gigabit**: 40-60 minutes (full 4.2GB transfer)
- **100Mbps**: 6-8 hours
- **25Mbps**: 24+ hours
- **Slow (<10Mbps)**: Use rebuild strategy instead

### Local Network/USB Transfer
- **USB 3.0**: 15-20 minutes
- **USB 2.0**: 45-60 minutes
- **Network share**: 30-45 minutes

## Success Confirmation

✅ **Migration Complete When:**
1. Chat application launches without errors
2. @aaron returns exactly 218 verses
3. /stats shows 166,395+ chunks
4. All 7 ChromaDB collections present
5. BGE-large model loads successfully
6. Optional: Ollama integration working (if desired)

---

**Next Steps After Migration:**
1. Update git remote if needed: `git remote set-url origin <new-url>`
2. Test all critical features with sample queries
3. Set up automated backups on new machine
4. Update documentation with new machine specifics

*Migration guide created: September 24, 2025*