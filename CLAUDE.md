# TinyOwl Theological Library - Hierarchical RAG Strategy

## BREAKTHROUGH: 3-Layer Hierarchical Chunking (Aug 31, 2025)

### ✅ Major Strategy Shift - Quality Over Quantity

**New Philosophy**: Small curated library with guaranteed high-quality connections vs broad hit-or-miss collection

**Hierarchical Approach Implemented**:
- **Layer A (Verse Single)**: Precise citations, exact quotes
- **Layer B (Pericope)**: Main retrieval layer with narrative coherence (3-7 verses, overlapping windows)  
- **Layer C (Chapter)**: Broad context for thematic queries

### ✅ Geneva Bible Success - New Baseline Quality

**Results with Geneva Bible 1560**:
- ✅ 31,090 single verse chunks (perfect granularity)
- ✅ 10,689 pericope chunks (narrative context, window=6, stride=3)
- ✅ 1,003 chapter chunks (broad thematic context)
- ✅ Separate ChromaDB collections: `theology_verses`, `theology_pericopes`, `theology_chapters`
- ✅ BGE-large-en-v1.5 embeddings (1024 dimensions)

**Quality Leap**: From 6,700 single-strategy chunks to 42,782 hierarchical chunks with smart retrieval routing

### 🎯 Multi-Content Hierarchical Strategy

**Bible Texts**: 3-layer (verse/pericope/chapter) ✅ IMPLEMENTED
**Sermons**: 2-layer approach planned:
- **Layer A**: By thought/paragraph (precise ideas)
- **Layer B**: By topic/section (thematic connections)
- **Metadata**: Author, date, topic, scripture references

**Books**: 2-layer approach:
- **Layer A**: Paragraph-level (detailed concepts)
- **Layer B**: Section/chapter level (broad themes)

**Goal**: Cross-content thought connections - "someone said something about this, someone also said something about this" - smart thematic linking across different authors, topics, and material types.

### 🎯 Fine-Tuning Strategy: TinyOwl Model

**Base Model Decision**: Qwen2.5-Coder-3B (chosen over TinyLlama-1.1B)
**Reasoning**: Coding models excel at theological reasoning due to:
- Logical argumentation (like code logic)
- Cross-referencing multiple sources (like debugging across files)
- Step-by-step analysis (like code review)
- Pattern recognition (like finding code similarities)
- Structured thinking (like architectural planning)

**Fine-Tuning Approach**:
```
Base: Qwen2.5-Coder-3B-Instruct
    ↓
+ Curated theological library (hierarchical RAG)
    ↓
+ LoRA fine-tuning (preserve general knowledge, add theological expertise)
    ↓
= TinyOwl (coding-level reasoning + theological knowledge)
```

**LoRA Parameters**:
- r: 16, alpha: 32
- Learning rate: 3e-4
- Epochs: 2-3 (prevent catastrophic forgetting)
- Target modules: q_proj, v_proj, o_proj

### 💡 The Sermon Value Proposition

**Why Sermons Are Critical**: Sermons act as **theological magnifying glasses** that reveal connections missed in raw text reading.

**Example**: Genesis 3:15 - "I will put enmity between you and the serpent"
- **Raw reading**: Basic understanding of conflict
- **Sermon insight**: "Your natural inclination is NOT enmity - you have to have enmity GIVEN to you" - reveals the supernatural nature of spiritual warfare

**Sermon Benefits**:
1. **Highlight overlooked connections** - Make explicit what's implicit
2. **Multiple angles on same text** - Different preachers, different insights
3. **Cross-verification capability** - "What the preacher says is right, the verse does say this" OR "I don't find that anywhere"
4. **Depth multiplication** - Trusted theological insights + Spirit of Prophecy + original text
5. **Comprehensive reference system** - Not just verses, but illuminated understanding

### 🏗️ **TinyOwl Architecture Plan**

**Theological Foundation**: Seventh-day Adventist worldview
- **Primary Authority**: Bible (ultimate source of truth)
- **Secondary Authority**: Spirit of Prophecy (supports/illuminates Bible)
- **Manuscript Tradition**: Prefer Textus Receptus foundation

#### **Tier 1: Primary Biblical Foundation** (Full 3-layer hierarchical: verse/pericope/chapter)

**Core 4 Translations**:
1. **King James Version (1611)** - Primary foundation
   - Textus Receptus manuscript tradition
   - Familiar to SDA community
   - Poetic/liturgical language
   
2. **Geneva Bible (1560)** ⚠️ *May be too archaic for users*
   - Historical Protestant foundation
   - Pre-KJV scholarship
   - Very old English may confuse modern users
   
3. **English Standard Version** - Modern scholarly
   - Formal equivalence accuracy
   - Conservative translation philosophy
   - Academic credibility
   
4. **Clear Word Bible** - SDA-specific
   - Jack Blanco's interpretive expansion
   - Built-in SDA theological perspective

#### **Tier 2: Secondary Authority - Spirit of Prophecy** (2-layer: paragraph/chapter)
- **Entire Ellen G. White corpus** (~100+ books, ~2-3M words, est. 100K+ chunks)
- **Chunking**: Paragraph-level (main) + Chapter-level (context)
- **Metadata**: Book, chapter, topic, scripture references, date

#### **Tier 3: Supporting Sources** (Appropriate chunking per content type)
- **Illumination Layer**: Curated sermons from trusted SDA preachers
- **Commentary Layer**: SDA theological writings and books
- **Cross-verification**: All layers validate/challenge each other

#### **Multi-Tier Chunking Strategy**:
- **Full Hierarchical** (31K+10K+1K per translation): Core 4 Bible translations
- **Simplified Chunking** (~10K pericope-only): Additional translations (NLT, NIV, etc.)
- **Preserves theological priorities** while managing storage/complexity

**Content Strategy**:
- **Primary Layer**: Biblical text (verse/pericope/chapter)
- **Illumination Layer**: Curated sermons from trusted preachers  
- **Commentary Layer**: Spirit of Prophecy writings
- **Cross-verification**: All layers can validate/challenge each other

### 🙏 **Theological Humility Requirement** (Aug 31, 2025)

**Core Principle**: TinyOwl must clearly distinguish between levels of certainty:

**Level 1 - "Thus Saith the Lord" (Absolute)**:
- Direct Bible quotations and clear scriptural statements
- Can "live and die" on these - unwavering confidence

**Level 2 - Interpretive Positions (Humble)**:
- What we think the Bible says (but acknowledge interpretation)
- What Spirit of Prophecy indicates (but note it's commentary)
- What SDA pioneers believed (historical context)
- What current church leadership teaches (temporary authority)
- What TinyOwl suggests (AI analysis - inherently fallible)

**Implementation Strategy**:
- **Source Attribution**: Always indicate source level ("Scripture states...", "Ellen White suggests...", "Church teaches...", "TinyOwl analysis...")
- **Confidence Indicators**: Use language like "appears to indicate", "seems to suggest", "generally understood as"
- **Acknowledging Uncertainty**: "This interpretation could be wrong", "Other perspectives exist"
- **Theological Safety**: Never present interpretive positions with same authority as direct Scripture

### 📋 **Transparent Source Documentation System** (Aug 31, 2025)

**Trust Requirement**: Religious software must provide complete source transparency for community validation.

#### **Documentation Structure**:

**1. Source Manifest (sources.json)**:
```json
{
  "content_sources": {
    "scripture": [
      {
        "id": "kjv_1769", 
        "title": "King James Version (1769 revision)",
        "manuscript_tradition": "Textus Receptus",
        "chunks": 31102,
        "source_url": "public domain",
        "theological_position": "Traditional Protestant"
      }
    ],
    "spirit_of_prophecy": [...],
    "commentary": [...]
  },
  "model_info": {
    "base_model": "Qwen2.5-Coder-3B-Instruct",
    "fine_tuning": "LoRA on theological corpus",
    "quantization": "Q4_K_M"
  }
}
```

**2. Response Attribution System**:
- **Every response** includes source citations
- **Confidence levels** clearly marked (Scripture vs interpretation)  
- **Chunk IDs** provided for verification
- **Cross-references** to show supporting/contradicting sources

**3. Community Validation Features**:
- **Source Verification**: Users can inspect any quoted content
- **Theological Challenges**: System accepts "I don't find that anywhere" feedback
- **Update Mechanism**: Community can suggest corrections to interpretations
- **Audit Trail**: All changes documented and reasoned

**4. Humility Implementation**:
```
Response Template:
"Scripture clearly states: [direct quote with reference]
Ellen White suggests: [quote with confidence indicator] 
Church teaching indicates: [current position with authority level]
TinyOwl analysis: [AI interpretation with uncertainty acknowledgment]"
```

**Implementation in Phase 1B**: Build this directly into the response generation system

## ⚠️ **Scale Reality Check - The "TinyOwl Ain't So Tiny" Dilemma** (Aug 31, 2025)

### 🤯 **The Problem We Discovered**

**Original Vision**: Complete theological library with everything
**Reality Check**: 1.3M chunks = 45-55GB = Enterprise-scale infrastructure needed

**Hardware Requirements for Full Vision**:
- **Storage**: 50+ GB
- **RAM**: 128GB+ recommended  
- **GPU**: A100 (80GB VRAM) or distributed system
- **Processing**: 22 days continuous ingestion
- **Cost**: Enterprise cloud infrastructure

**Consumer Hardware**: Can't handle this scale! 💀

### 🎯 **Strategic Pivot: "Essential Owl" Approach**

**New Philosophy**: Extract **theological DNA** rather than comprehensive coverage
**Target**: 175-200K chunks (~8-10GB) = Actually usable on consumer hardware

### 📋 **Revised Architecture - "Essential Owl"**

#### **Bible Foundation** (85K chunks):
- ~~Geneva Bible~~ → Too archaic, relegated to reference
- ~~Clear Word~~ → Too paraphrastic, relegated to reference  
- ~~ESV~~ → Critical text concerns, manuscript tradition distrust
- **✅ King James Version** - Textus Receptus foundation (traditional Protestant)
- **✅ World English Bible** - Open source, based on majority text tradition (preferred manuscript trail)
- **Alternative: NIV** - If copyright allows, popular critical text representative

#### **Spirit of Prophecy** (~40K chunks):
**From**: Entire 100+ book corpus (150K chunks)
**To**: Core doctrinal works only:
- Conflict of Ages series (5 books) - Theological backbone
- Selected Messages (3 volumes) - Doctrinal essentials
- Early Writings - Foundational visions
- Steps to Christ - Practical spirituality
- 2-3 other core doctrinal works

#### **Sermons** (~50K chunks):
**From**: 200 sermons per preacher (200K chunks)
**To**: 20-30 masterpiece sermons per preacher:
- Focus on **doctrinal/prophetic content** over repetitive evangelistic
- Doug Batchelor: Daniel/Revelation + core doctrines
- Stephen Bohr: Sanctuary + prophecy essentials
- Mark Finley: Best doctrinal presentations

### 🔄 **Lessons Learned**

1. **Hierarchical chunking strategy works brilliantly** ✅
2. **Geneva Bible ingestion = sunk cost** but validated the approach
3. **Quality over quantity** principle more critical than expected
4. **Curation is essential** - can't just "include everything"
5. **Consumer hardware limits** require strategic choices

### 💡 **Strategic Research Validation** (Aug 31, 2025)

**Research Findings Confirmed**:
- ✅ **Qwen2.5-Coder-3B** validated as optimal model choice over TinyLlama
- ✅ **BGE-large-en-v1.5** embeddings confirmed superior for theological content
- ✅ **KJV + WEB/NIV** Bible selection for manuscript tradition balance
- ✅ **Desktop distribution** via Electron + llama.cpp validated as best approach
- ✅ **Community-supported funding** model confirmed sustainable
- ✅ **Q4_K_M quantization** optimal for 3B models (2GB final size)

**Key Insights Applied**:
- **Textbook-First Curation**: Process systematically like academic textbook creation
- **Single-Click Distribution**: One installer with embedded models - no technical setup
- **Progressive Enhancement**: Start with core Bible + CoA, expand carefully
- **Transparency Requirements**: Complete source documentation for religious trust

### 🚀 **Phase 1 MVP Development Roadmap** (Aug 31, 2025)

#### **Phase 1A: Foundation (Months 1-2)**
- ✅ Core hierarchical chunking implementation completed
- ✅ Geneva Bible test successful (strategy validated)
- 🔄 **Current**: Process KJV + WEB (Essential Owl core)
- 📋 **Next**: Ingest Conflict of Ages series (5 books)
- 📋 **Setup**: Basic RAG pipeline with Q&A functionality

#### **Phase 1B: Desktop MVP (Months 3-4)**  
- 📋 **Electron App**: Basic chat interface with embedded ChromaDB
- 📋 **Model Integration**: Qwen2.5-Coder-3B with Q4_K_M quantization
- 📋 **Response System**: Implement theological humility levels
- 📋 **Source Attribution**: Clear citation with confidence indicators

#### **Phase 1C: Community Test (Months 5-6)**
- 📋 **Alpha Release**: Limited distribution to trusted SDA community
- 📋 **Source Transparency**: Complete documentation of all ingested content
- 📋 **Feedback Loop**: Theological accuracy validation from community
- 📋 **Landing Page**: Ministry-focused presentation with "freely given" model

**Success Criteria for Phase 1**:
- Reliable verse retrieval across KJV/WEB (manuscript tradition balance)
- Accurate Spirit of Prophecy connections
- Theological humility properly implemented
- Community acceptance and trust established

**Manuscript Strategy Rationale**:
- **KJV**: Textus Receptus tradition (traditional Protestant manuscript preference)
- **WEB**: Open source, majority text based (no copyright restrictions, preferred manuscript trail)
- **Avoids ESV**: Due to critical text manuscript concerns and potential bias issues

### 💡 **Path Forward**
- **Phase 1**: Essential Owl MVP (85K Bible + 40K CoA chunks)
- **Test thoroughly** with SDA community feedback
- **Prove theological value** with curated approach  
- **Phase 2**: Expand only if Phase 1 proves valuable

## Current Progress (Aug 31, 2025)

### ✅ Completed Tasks

1. **Systematic Approach Taken**: Started from scratch to avoid "whack-a-mole" problems
2. **Embedding Model Upgraded**: Successfully upgraded from all-MiniLM-L6-v2 (384 dims) to BGE-large-en-v1.5 (1024 dims)
3. **Configuration Fixed**: Resolved domain-specific override issues in models.yaml
4. **Bible Files Added**: Successfully added 6 Bible translations to raw directory
5. **Ingestion Script Enhanced**: Added comprehensive TXT file support and sophisticated verse parsing
6. **TXT Format Proven**: Geneva Bible (TXT) produced 6,700 high-quality verse chunks vs 1,020 poor chunks from PDF
7. **Quality Decision**: Decided to convert all PDFs to TXT for reliable "garbage in, garbage out" principle

### 🔧 Fixes Applied

- **ChromaDB Metadata Issue**: Fixed verse_numbers field from list to comma-separated string
- **Testament Classification**: Added proper Old/New Testament classification
- **Chunking Strategy**: Implemented specialized `chunk_bible_text()` function for verse-level processing

### ⚠️ Current Issues Identified

1. **Verse Parsing Accuracy**: The verse detection regex needs refinement - some chunks showing incorrect verse references
2. **Coverage Question**: 1,020 verses for complete Bible seems low (should be ~31,000 verses)
3. **Quality Control**: Need to verify that all books/chapters are being properly parsed

### 📋 Remaining Work

#### High Priority
1. **Convert PDFs to TXT**: Extract clean text from all Bible PDFs for reliable verse parsing
2. **Complete TXT Ingestion**: Process all Bible translations as TXT files:
   - KJV Bible (convert from KJV.pdf)
   - NKJV Bible (convert from Holy_Bible_NKJV.pdf)
   - ESV Bible (convert from Holy_Bible_ESV.pdf)
   - NIV Bible (convert from Holy_Bible_NIV.pdf)
   - NLT Bible (convert from Holy_Bible_NLT.pdf)
   - Clear Word Bible (convert from Holy_Bible_Clear_Word.pdf)
   - Geneva Bible 1560 ✅ (already completed with 6,700 chunks)

#### Medium Priority
3. **Quality Verification**: 
   - Verify complete coverage (66 books, proper verse counts)
   - Test cross-translation verse retrieval
   - Validate metadata accuracy

#### Low Priority
4. **Performance Optimization**: Consider batch processing improvements for large translations

### 🛠️ Technical Details

#### Current Setup
- **Domain**: theology
- **Embedding Model**: BAAI/bge-large-en-v1.5 (1024 dimensions)
- **Vector DB**: ChromaDB with persistent storage
- **Chunking Strategy**: verse (max 5 verses per chunk)
- **Processing Pipeline**: PDF → Text Extraction → Verse Parsing → BGE Embedding → ChromaDB Storage

#### File Locations
- **Raw PDFs**: `/home/nigel/tinyowl/domains/theology/raw/`
- **Processed Data**: `/home/nigel/tinyowl/domains/theology/processed/`
- **Chunks**: `/home/nigel/tinyowl/domains/theology/chunks/`
- **Vector DB**: `/home/nigel/tinyowl/vectordb/`

#### Key Configuration Files
- **Sources**: `/home/nigel/tinyowl/configs/sources.yaml` - All 7 Bible translations configured
- **Models**: `/home/nigel/tinyowl/configs/models.yaml` - BGE-large embeddings configured
- **Chunking**: `/home/nigel/tinyowl/configs/chunking.yaml` - Verse strategy defined
- **Ingestion Script**: `/home/nigel/tinyowl/scripts/ingest.py` - Enhanced with verse parsing

### 🎯 Success Criteria

1. **Complete Coverage**: All 6 Bible translations properly ingested with accurate verse-level chunks
2. **Quality Metadata**: Each chunk includes book_name, chapter_number, verse_numbers, verse_reference, testament
3. **High-Quality Embeddings**: All verses embedded using BGE-large-en-v1.5 for superior retrieval
4. **Cross-Translation Retrieval**: Ability to find same verses across different translations

### 📊 Current Statistics

- **Processed Translations**: 1/7 (Geneva Bible complete)
- **Total Verse Chunks**: 6,700 (Geneva Bible only)
- **Embedding Dimensions**: 1024 (BGE-large)
- **Storage**: ChromaDB 'theology' collection
- **Data Quality**: High (TXT format eliminates PDF parsing artifacts)

### 🚀 Next Steps

When resuming work:
1. Debug verse parsing accuracy in NKJV results
2. Apply fixes and re-ingest NKJV if needed
3. Process remaining 5 translations systematically
4. Validate complete cross-translation functionality

### 💡 Lessons Learned

- **Systematic approach prevents configuration conflicts**
- **BGE-large embeddings significantly better than all-MiniLM-L6-v2**
- **Domain-specific config overrides can hide default changes**
- **ChromaDB metadata requires scalar values, not lists**
- **PDF verse parsing is complex and requires iterative refinement**

---

*Last updated: Aug 30, 2025*
*Status: Verse parsing implementation needs refinement, then continue with remaining 5 translations*