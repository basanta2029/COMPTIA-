# CompTIA Security+ Data Cleaning Pipeline

## Overview

This pipeline processes raw CompTIA Security+ course materials (video transcripts, text documents) into a clean, structured format optimized for **RAG (Retrieval Augmented Generation)** implementation with **summary-indexed vector embeddings**.

## Data Processing Results

### Statistics (Chapters 1-4)

- **Total Documents Processed**: 112
- **Total Content Chunks**: 701
- **Total Words**: 119,418
- **Average Chunks per Document**: 6.3

### By Chapter

| Chapter | Documents | Chunks | Words | Video | Text |
|---------|-----------|--------|-------|-------|------|
| 01 - Security Concepts | 9 | 54 | 9,289 | 6 | 3 |
| 02 - Threats, Vulnerabilities & Mitigations | 19 | 121 | 24,171 | 11 | 8 |
| 03 - Cryptographic Solutions | 34 | 229 | 34,048 | 22 | 12 |
| 04 - Identity & Access Management | 50 | 297 | 51,910 | 31 | 19 |

## Pipeline Components

### 1. Data Cleaner (`data_cleaner.py`)

**Purpose**: Extract and normalize content from raw transcript files

**Features**:
- Parses filenames to extract metadata (chapter, section, title, type)
- Removes timestamp markers from video transcripts
- Preserves section headers for semantic chunking
- Cleans text documents while maintaining structure
- Outputs structured JSON with metadata and chunks

**Skipped Files**:
- Empty exam files (50 files) - interactive web-based content
- Empty simulation files - hands-on lab content

**Output Structure**:
```
data_clean/
├── 01_Security_Concepts/
│   ├── video/
│   │   └── 1.1.1_The_Security_Landscape.json
│   ├── text/
│   │   └── 1.1.3_Security_Introduction_Facts.json
│   └── chapter_overview.json
├── 02_Threats_Vulnerabilities_and_Mitigations/
├── 03_Cryptographic_Solutions/
└── 04_Identity_and_Access_Management/
```

### 2. Summarizer (`summarizer.py`)

**Purpose**: Generate summaries optimized for RAG embeddings

**Features**:
- **Chunk-level summaries**: Extractive summarization for each content chunk
- **Document-level summaries**: Overall summary for entire document
- **Keyword-aware**: Prioritizes security-related terminology
- **Context preservation**: Includes section headers in summaries

**Summarization Strategy**:
- Extracts 2-3 key sentences per chunk
- Prioritizes sentences with security keywords
- Includes section headers for context
- Optimized length for embedding models (typically 20-50 words)

### 3. Validator (`validate_data.py`)

**Purpose**: Ensure data quality and RAG readiness

**Validation Checks**:
- ✓ JSON structure integrity
- ✓ Required fields present (metadata, content, chunks, summaries)
- ✓ Non-empty content and summaries
- ✓ Proper metadata structure
- ✓ Document-level summaries exist

**Quality Metrics**:
- Average chunk length
- Average summary length
- Total word counts
- Chunks per document

## Output Data Format

### JSON Structure

```json
{
  "metadata": {
    "chapter_num": "1",
    "section_num": "1.1.1",
    "title": "The Security Landscape",
    "content_type": "video",
    "filename": "1.1.1_The_Security_Landscape_[video].txt",
    "file_path": "/path/to/raw/file.txt",
    "word_count": 687,
    "has_content": true
  },
  "full_content": "Complete document text...",
  "document_summary": "High-level summary of entire document...",
  "chunks": [
    {
      "chunk_id": "1.1.1_chunk_1",
      "content": "Chunk content text...",
      "summary": "Concise summary for embedding...",
      "metadata": { /* same as document metadata */ },
      "section_header": "Introduction",
      "timestamp_range": "00:00-00:24"  // video only
    }
  ],
  "num_chunks": 5
}
```

## Usage

### Run Complete Pipeline

```bash
# Step 1: Clean raw data
python3 data_cleaner.py

# Step 2: Generate summaries
python3 summarizer.py

# Step 3: Validate output
python3 validate_data.py
```

### Individual Steps

```python
from pathlib import Path
from data_cleaner import DataCleaner

# Initialize cleaner
cleaner = DataCleaner('data_raw', 'data_clean')

# Process specific chapters
cleaner.run(chapters=['01_Security_Concepts'])
```

## RAG Implementation Guide

### 1. Embedding Strategy

**Recommended**: Embed the `summary` field for each chunk
- Summaries are optimized for semantic search
- Include key concepts and security terminology
- Length-optimized for embedding models

**Alternative**: Embed full `content` for detailed retrieval
- Use for more granular search
- May require chunking strategy adjustment

### 2. Metadata Filtering

Use metadata for:
- **Chapter filtering**: `metadata.chapter_num`
- **Content type filtering**: `metadata.content_type` (video/text)
- **Section routing**: `metadata.section_num`
- **Title-based search**: `metadata.title`

### 3. Hierarchical Retrieval

**Level 1**: Document-level summary
- Use `document_summary` for high-level topic matching
- Quick filtering of relevant documents

**Level 2**: Chunk-level retrieval
- Use chunk `summary` for specific concept retrieval
- Return full `content` for context

### 4. Suggested Vector Database Schema

```python
{
    "id": "chunk_id",
    "vector": [embedded_summary],
    "payload": {
        "content": "full chunk content",
        "summary": "chunk summary",
        "section_header": "section name",
        "chapter": "chapter_num",
        "section": "section_num",
        "title": "document title",
        "content_type": "video/text",
        "document_summary": "doc-level summary"
    }
}
```

## Next Steps for RAG Implementation

1. **Generate Embeddings**:
   - Use OpenAI `text-embedding-3-small` or similar
   - Embed chunk summaries for efficient retrieval
   - Store in vector database (Pinecone, Weaviate, Qdrant, etc.)

2. **Build Summary Index**:
   - Create hierarchical index: document → chunks
   - Enable multi-stage retrieval

3. **Implement Retrieval**:
   - Semantic search on summaries
   - Metadata filtering for targeted results
   - Return full content for LLM context

4. **Generate Responses**:
   - Use retrieved chunks as context
   - Include section headers for structure
   - Reference chapter/section numbers

## Data Quality Assurance

✅ **All validation checks passed**:
- 112/112 documents valid
- 701/701 chunks have summaries
- All metadata complete
- Zero structural issues

✅ **RAG Ready**:
- Proper JSON structure
- Complete summaries for embeddings
- Rich metadata for filtering
- Semantic chunking preserved

## File Locations

```
CompTia/
├── data_raw/                    # Original transcript files
├── data_clean/                  # Processed JSON files
│   ├── 01_Security_Concepts/
│   ├── 02_Threats_Vulnerabilities_and_Mitigations/
│   ├── 03_Cryptographic_Solutions/
│   ├── 04_Identity_and_Access_Management/
│   └── validation_report.json  # Quality validation report
├── data_cleaner.py             # Step 1: Clean & structure
├── summarizer.py               # Step 2: Generate summaries
├── validate_data.py            # Step 3: Validate quality
└── README_DATA_CLEANING.md     # This file
```

## Key Features for RAG

1. **Semantic Chunking**: Content split by natural section boundaries
2. **Summary Indexing**: Optimized summaries for efficient retrieval
3. **Rich Metadata**: Chapter, section, type for filtering
4. **Section Headers**: Preserved for context and structure
5. **Document Summaries**: High-level topic matching
6. **Validated Quality**: Zero issues, production-ready

---

**Status**: ✅ Data cleaning complete and validated
**Total Processing Time**: ~2 minutes for 165 files
**Next Step**: Implement embedding generation and vector database integration
