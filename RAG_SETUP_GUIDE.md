# CompTIA Security+ RAG System - Setup Guide

## Overview
This RAG system uses **summary-indexed retrieval** where embeddings are generated from combined text (section_header + summary + content) for rich semantic search.

## Architecture
```
User Query
→ Voyage AI Embedding
→ Qdrant Vector Search
→ Retrieve Full Content
→ Claude 3.5 Sonnet Response
```

## Prerequisites
- Python 3.8+
- Docker & Docker Compose
- API Keys:
  - Anthropic API key (for Claude summaries & responses)
  - Voyage AI API key (for embeddings)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Set Up Environment Variables

Create or update `.env` file:
```bash
ANTHROPIC_API_KEY=your-anthropic-key-here
VOYAGE_AI_KEY=your-voyage-ai-key-here
```

## Step 3: Data Preparation (Already Complete)

✅ Raw data cleaned (112 documents, 701 chunks)
✅ AI summaries generated with Claude 3.5 Sonnet
✅ Data stored in `data_clean/` with structured JSON

## Step 4: Start Qdrant Vector Database

```bash
# Start Qdrant using Docker Compose
docker-compose up -d

# Verify it's running
curl http://localhost:6333
```

Qdrant will be available at:
- HTTP API: `http://localhost:6333`
- gRPC API: `localhost:6334`
- Web UI: `http://localhost:6333/dashboard`

## Step 5: Generate Embeddings

Generate embeddings for all 701 chunks using Voyage AI:

```bash
# Using voyage-3-lite (512 dimensions, cheaper)
python3 embedding_generator.py --model voyage-3-lite

# OR using voyage-3 (1024 dimensions, better quality)
python3 embedding_generator.py --model voyage-3 --embedding-dim 1024
```

**Cost Estimates:**
- `voyage-3-lite`: ~$0.05-0.10 for all 701 chunks
- `voyage-3`: ~$0.10-0.20 for all 701 chunks

**Output:** `embeddings.json` (~50-100 MB)

## Step 6: Upload Embeddings to Qdrant

```bash
# For voyage-3-lite (512 dims)
python3 vector_db_manager.py --action upload --embedding-dim 512

# For voyage-3 (1024 dims)
python3 vector_db_manager.py --action upload --embedding-dim 1024
```

**What this does:**
1. Creates collection `comptia_security_plus`
2. Uploads all 701 embeddings with metadata
3. Creates indexes for filtering by chapter/section/type

## Step 7: Verify Vector Database

```bash
# Check collection info
python3 vector_db_manager.py --action info

# Access Qdrant dashboard
open http://localhost:6333/dashboard
```

Expected output:
```
collection_name: comptia_security_plus
vectors_count: 701
vector_size: 512  (or 1024 for voyage-3)
distance: Cosine
status: green
```

## Step 8: Test RAG Retrieval (Next Steps)

Once embeddings are uploaded, you can:

1. **Test semantic search:**
   ```python
   from rag_retriever import RAGRetriever

   retriever = RAGRetriever()
   results = retriever.search("What is phishing?", top_k=5)
   ```

2. **Run API server:**
   ```bash
   python3 api_server.py
   ```

3. **Launch Streamlit UI:**
   ```bash
   streamlit run app.py
   ```

## Project Structure

```
CompTia/
├── data_raw/                    # Original transcripts
├── data_clean/                  # Cleaned JSON with AI summaries
│   ├── 01_Security_Concepts/
│   ├── 02_Threats_Vulnerabilities_and_Mitigations/
│   ├── 03_Cryptographic_Solutions/
│   └── 04_Identity_and_Access_Management/
├── data_clean_backup/          # Backup before AI summarization
├── embeddings.json             # Generated embeddings (will be created)
├── .env                        # API keys
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Qdrant setup
│
├── data_cleaner.py             # ✅ Data cleaning pipeline
├── claude_summarizer.py        # ✅ AI summarization
├── embedding_generator.py      # ✅ Voyage AI embedding generation
├── vector_db_manager.py        # ✅ Qdrant database manager
│
├── rag_retriever.py            # 🔄 Semantic search & retrieval (next)
├── llm_engine.py               # 🔄 Claude integration (next)
├── api_server.py               # 🔄 FastAPI backend (next)
└── app.py                      # 🔄 Streamlit UI (next)
```

## Data Structure

Each chunk in `embeddings.json`:
```json
{
  "chunk_id": "1.1.1_chunk_1",
  "embedding": [0.123, -0.456, ...],  // 512 or 1024 floats
  "content": "Full original content...",
  "summary": "AI-generated summary...",
  "section_header": "The Security Landscape",
  "metadata": {
    "chapter_num": "1",
    "section_num": "1.1.1",
    "title": "The Security Landscape",
    "content_type": "video",
    "filename": "1.1.1_The_Security_Landscape_[video].txt",
    "word_count": 687
  }
}
```

## Qdrant Collection Schema

```python
{
  "vectors": {
    "size": 512,  # or 1024
    "distance": "Cosine"
  },
  "payload": {
    "chunk_id": str,
    "content": str,
    "summary": str,
    "section_header": str,
    "metadata": {
      "chapter_num": str,
      "section_num": str,
      "title": str,
      "content_type": str,  # "video" or "text"
      "filename": str,
      "word_count": int
    }
  },
  "indexed_fields": [
    "metadata.chapter_num",
    "metadata.section_num",
    "metadata.content_type"
  ]
}
```

## Usage Examples

### 1. Basic Search
```python
from rag_retriever import RAGRetriever

retriever = RAGRetriever()
results = retriever.search("What is two-factor authentication?", top_k=5)

for result in results:
    print(f"Section: {result.section_header}")
    print(f"Summary: {result.summary}")
    print(f"Score: {result.score}")
    print("---")
```

### 2. Filtered Search
```python
# Search only in Chapter 3 (Cryptography)
results = retriever.search(
    query="Explain AES encryption",
    top_k=5,
    chapter_filter="3"
)

# Search only video content
results = retriever.search(
    query="What is PKI?",
    top_k=5,
    content_type_filter="video"
)
```

### 3. Full RAG Pipeline
```python
from rag_retriever import RAGRetriever
from llm_engine import LLMEngine

retriever = RAGRetriever()
llm = LLMEngine()

# Search for relevant chunks
query = "Explain the difference between symmetric and asymmetric encryption"
results = retriever.search(query, top_k=5)

# Generate response with Claude
response = llm.generate_answer(query, results)
print(response)
```

## Troubleshooting

### Qdrant Connection Issues
```bash
# Check if Qdrant is running
docker ps | grep qdrant

# Restart Qdrant
docker-compose restart

# Check logs
docker-compose logs qdrant
```

### Embedding Generation Errors
- **API Key Error:** Check `.env` file has valid `VOYAGE_AI_KEY`
- **Rate Limiting:** Script has built-in delays, but you can adjust batch size
- **Memory Issues:** Embeddings file can be large (~100 MB), ensure enough disk space

### Vector Upload Issues
- **Dimension Mismatch:** Ensure `--embedding-dim` matches your model choice
- **Collection Already Exists:** Use `--recreate` flag to reset collection

## Performance Optimization

1. **Embedding Model Choice:**
   - `voyage-3-lite` (512 dims): Faster, cheaper, good for most queries
   - `voyage-3` (1024 dims): Better quality, more expensive

2. **Batch Sizes:**
   - Embedding generation: 128 chunks/request (max for Voyage AI)
   - Vector upload: 100 points/batch (configurable)

3. **Query Optimization:**
   - Use metadata filters to reduce search space
   - Adjust `top_k` based on context window needs (5-10 recommended)

## Next Steps

After completing the setup:
1. ✅ Create `rag_retriever.py` for semantic search
2. ✅ Build `llm_engine.py` for Claude integration
3. ✅ Implement `api_server.py` with FastAPI
4. ✅ Deploy `app.py` Streamlit UI

## Resources
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Anthropic Claude API](https://docs.anthropic.com/)
