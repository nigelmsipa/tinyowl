# TinyOwl Ritual of Curation
## Bulletproof Quality Control for Every Source

This checklist ensures every source added to TinyOwl meets the highest quality standards and maintains theological integrity.

## 🎯 **Pre-Ingestion Checklist**

### 1. Source Documentation
- [ ] **Source sheet created** with complete metadata
  - [ ] Title, author, publication year
  - [ ] Authority level (Scripture/SOP/Commentary) 
  - [ ] License/copyright status verified
  - [ ] Theological position documented
  - [ ] Reason for inclusion stated

### 2. Quality Assessment
- [ ] **Content review completed**
  - [ ] Theological accuracy verified by qualified reviewer
  - [ ] Doctrinal alignment with SDA worldview confirmed
  - [ ] No heretical or questionable content identified
  - [ ] Historical context and reliability assessed

### 3. Format Preparation
- [ ] **Source converted to clean format**
  - [ ] TXT/HTML/Markdown format (preferred over PDF)
  - [ ] Character encoding verified (UTF-8)
  - [ ] OCR quality checked (if applicable)
  - [ ] Formatting artifacts removed

## 📋 **Ingestion Process Checklist**

### 4. Text Normalization
- [ ] **Run through normalization pipeline**
  - [ ] Unicode normalization applied (NFKC)
  - [ ] Smart quotes converted to straight quotes
  - [ ] Em/en dashes converted to hyphens
  - [ ] Whitespace collapsed and cleaned
  - [ ] Ornamental elements removed

### 5. Reference Extraction (for non-Scripture sources)
- [ ] **Scripture references identified and normalized**
  - [ ] All Bible references extracted using scripture_extractor.py
  - [ ] References normalized to OSIS format
  - [ ] Confidence scores reviewed (>0.8 preferred)
  - [ ] Cross-reference accuracy spot-checked

### 6. Chunking Strategy Selection
- [ ] **Appropriate chunking method chosen**
  - [ ] **Scripture**: 3-layer hierarchical (verse/pericope/chapter)
  - [ ] **Spirit of Prophecy**: 2-layer (paragraph/chapter) 
  - [ ] **Sermons**: 2-layer (paragraph/section) with scripture pre-links
  - [ ] **Books**: 2-layer (paragraph/section)
  - [ ] Chunk size validated (not too large/small)

### 7. Metadata Assignment
- [ ] **Complete metadata assigned to all chunks**
  - [ ] Source identification (id, title, author)
  - [ ] Authority level classification
  - [ ] Content type and structure tags
  - [ ] Scripture references (for non-Bible content)
  - [ ] Topical tags and categories
  - [ ] Creation timestamp

## ✅ **Post-Processing Validation**

### 8. Coverage Verification
- [ ] **Run canonical validation** (for Scripture)
  - [ ] All 66 books present
  - [ ] 31,102 verses accounted for
  - [ ] No missing chapters or verses
  - [ ] No duplicate OSIS IDs
  - [ ] Validation report reviewed and approved

### 9. Quality Control Sampling
- [ ] **Spot-check 10 random chunks**
  - [ ] Content accuracy verified
  - [ ] Metadata correctness confirmed
  - [ ] Scripture references validated
  - [ ] Cross-links functional
  - [ ] No truncation or corruption

### 10. Pre-linking Computation
- [ ] **Nearest neighbor pre-computation completed**
  - [ ] Scripture pericopes linked to sermon chunks
  - [ ] Cross-reference networks established
  - [ ] Link quality spot-checked (relevance >0.7)
  - [ ] Reciprocal links verified

## 🔍 **Final Quality Assurance**

### 11. Embedding Generation
- [ ] **Vector embeddings created**
  - [ ] BGE-large-en-v1.5 embeddings generated
  - [ ] Embedding quality verified (no NaN/infinite values)
  - [ ] Dimensionality confirmed (1024-dim)
  - [ ] Collection storage successful

### 12. Integration Testing
- [ ] **System integration verified**
  - [ ] Retrieval accuracy tested (sample queries)
  - [ ] Cross-collection search functional
  - [ ] Response generation includes new source
  - [ ] Authority levels properly recognized
  - [ ] Performance impact acceptable

### 13. Evaluation Harness
- [ ] **Run evaluation suite**
  - [ ] Coverage tests pass (100%)
  - [ ] Retrieval tests pass (>95%)
  - [ ] Answer quality maintained (>90%)
  - [ ] Performance targets met (<1.5s p95)
  - [ ] No regressions detected

## 📝 **Documentation and Logging**

### 14. Record Keeping
- [ ] **Update master source registry** (`sources.json`)
  - [ ] Source metadata recorded
  - [ ] Chunk count documented
  - [ ] Processing date logged
  - [ ] Quality scores recorded

### 15. Change Log
- [ ] **Document changes** (`CHANGES.md`)
  - [ ] What was added and why
  - [ ] Impact on system metrics
  - [ ] Any issues encountered
  - [ ] Recommendations for future

### 16. Backup and Version Control
- [ ] **Commit changes to git**
  - [ ] All new files committed
  - [ ] Configuration updates included
  - [ ] Meaningful commit message
  - [ ] Tagged with version number (if milestone)

## 🚨 **Failure Protocols**

### If Any Step Fails:
1. **STOP** - Do not proceed to next step
2. **Document** the failure in detail
3. **Fix** the underlying issue
4. **Re-run** from the failed step
5. **Verify** the fix didn't break previous steps
6. **Continue** only when all checks pass

### Critical Failure Points:
- **Coverage <100%**: Scripture sources must be complete
- **Validation errors**: Fix all errors before embedding
- **Quality degradation**: Investigation required if metrics drop >5%
- **Performance regression**: Optimization needed if response time >2x

## 📊 **Success Metrics**

### Source Quality Indicators:
- Coverage: 100% (Scripture sources)
- Reference accuracy: >95% 
- Chunk quality: >90% spot-check success
- Retrieval relevance: >85% average

### System Health Post-Addition:
- Overall evaluation score: >90%
- Response time: <1.5s p95
- Answer accuracy: >90%
- Source attribution: 100%

## 🎉 **Completion Ceremony**

When all checks pass:
- [ ] **Add to live system**
- [ ] **Update documentation**
- [ ] **Notify team/community** (if applicable)
- [ ] **Celebrate** the quality achievement! 🎊

---

## 📚 **Reference Documents**

- `configs/osis_canonical.yaml` - Canonical reference standards
- `scripts/canonical_validator.py` - Validation tools
- `scripts/evaluation_harness.py` - Quality testing
- `scripts/text_normalizer.py` - Processing pipeline
- `docs/authority_levels.md` - Theological authority guidelines

## 💡 **Quality Philosophy**

> "Garbage in, garbage out" - Every shortcut in curation multiplies downstream.
> "Measure twice, cut once" - Thorough validation prevents expensive fixes later.
> "Trust but verify" - Even trusted sources need systematic quality control.

**Remember**: Each source added becomes part of TinyOwl's theological DNA. Maintain the highest standards to serve the community faithfully.

---
*Last updated: Sept 1, 2025*
*Version: 1.0 - Foundation Architecture*