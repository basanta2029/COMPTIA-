# CompTIA Security+ RAG System

A complete **Retrieval Augmented Generation (RAG)** system for CompTIA Security+ certification Q&A using summary-indexed vector retrieval.

## 🏗️ Architecture

```
User Query
    ↓
[OpenAI Embeddings] → Query Vector (1536-dim)
    ↓
[Qdrant Vector DB] → Top-k Similar Documents
    ↓
[Context Assembly] → Section Header + Summary + Full Text
    ↓
[Claude Sonnet 4] → Generated Answer
    ↓
Response with Sources
```

## ✨ Features

- **Summary-Indexed Retrieval**: Embeds combined text (header + summary + content) for rich semantic search
- **Qdrant Vector Database**: 701 documents with 1536-dimensional embeddings
- **Claude Sonnet 4**: High-quality answer generation
- **Metadata Filtering**: Filter by chapter and content type (video/text)
- **Multiple Interfaces**: CLI, API, and Web UI
- **Source Citations**: Every answer includes source documents with scores

## 📊 Dataset

- **Chapters**: 1-4 of CompTIA Security+ training materials
- **Content Types**: Video transcripts and text documents
- **Total Chunks**: 701 semantically chunked documents
- **AI Summaries**: Generated with Claude for each chunk
- **Embeddings**: OpenAI text-embedding-3-small (1536 dimensions)

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start Qdrant (Docker required)
docker-compose up -d
```

### 2. Environment Setup

Create `.env` file:

```bash
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
```

### 3. Run the System

#### Option A: Interactive CLI Testing

```bash
# Interactive mode (ask custom questions)
python3 test_rag.py --mode interactive

# Run test suite (10 sample questions)
python3 test_rag.py --mode suite

# Single query
python3 test_rag.py --mode single --query "What is phishing?" --k 3
```

#### Option B: FastAPI Server

```bash
# Start API server
python3 api_server.py --host 0.0.0.0 --port 8000

# Access API docs
open http://localhost:8000/docs
```

#### Option C: Streamlit Web UI

```bash
# Start Streamlit app
streamlit run app.py

# Access UI
open http://localhost:8501
```

## 📁 Project Structure

```
CompTia/
├── data_raw/              # Raw training materials (chapters 1-4)
├── data_clean/            # Cleaned + summarized JSON files
├── embeddings.json        # OpenAI embeddings (32.51 MB)
├── docker-compose.yml     # Qdrant deployment
├── .env                   # API keys
│
├── Core RAG Components:
│   ├── rag_retriever.py      # Query embedding + Qdrant search
│   ├── llm_engine.py          # Claude answer generation
│   ├── rag_pipeline.py        # Complete Q&A pipeline
│   └── vector_db_manager.py   # Qdrant client wrapper
│
├── Data Pipeline:
│   ├── data_cleaner.py               # Raw data → cleaned chunks
│   ├── claude_summarizer.py          # AI summarization
│   └── embedding_generator_openai.py # Embedding generation
│
├── Interfaces:
│   ├── test_rag.py        # CLI testing interface
│   ├── api_server.py      # FastAPI REST API
│   └── app.py             # Streamlit web UI
│
└── requirements.txt       # Python dependencies
```

## 🔧 Core Components

### 1. RAG Retriever (`rag_retriever.py`)

Handles query embedding and vector search:

```python
from rag_retriever import RAGRetriever

retriever = RAGRetriever()

# Retrieve top-k documents
results, context = retriever.retrieve_level_two(
    query="What is phishing?",
    k=3,
    chapter_filter="1"  # Optional
)
```

### 2. LLM Engine (`llm_engine.py`)

Claude-powered answer generation:

```python
from llm_engine import LLMEngine

engine = LLMEngine(model="claude-sonnet-4-20250514")

# Generate answer from context
answer = engine.answer_query_level_two(
    query="What is phishing?",
    context=context  # From retriever
)
```

### 3. RAG Pipeline (`rag_pipeline.py`)

Complete end-to-end Q&A:

```python
from rag_pipeline import RAGPipeline

pipeline = RAGPipeline()

# One-line Q&A
response = pipeline.query(
    query="What is phishing?",
    k=3,
    chapter_filter="1"
)

print(response.answer)
print(f"Sources: {response.num_sources}")
```

### 4. Vector DB Manager (`vector_db_manager.py`)

Qdrant client wrapper:

```python
from vector_db_manager import VectorDBManager

db = VectorDBManager(
    collection_name="comptia_security_plus",
    embedding_dim=1536
)

# Search with filters
results = db.search(
    query_vector=embedding,
    top_k=5,
    chapter_filter="1"
)
```

## 🌐 API Endpoints

### FastAPI Server (`api_server.py`)

**POST /query** - Complete Q&A

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is phishing?",
    "k": 3,
    "chapter_filter": "1"
  }'
```

**POST /search** - Semantic search only (no LLM)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "encryption",
    "k": 5
  }'
```

**GET /health** - Health check

```bash
curl http://localhost:8000/health
```

**GET /chapters** - Available chapters

```bash
curl http://localhost:8000/chapters
```

## 💻 Streamlit UI (`app.py`)

Interactive web interface with:

- 💬 **Chat Interface**: Ask questions naturally
- 🎛️ **Filters**: Chapter, content type, k value
- 📊 **Source Display**: View retrieved documents with scores
- ⚙️ **LLM Settings**: Adjust temperature and max tokens
- 💡 **Sample Questions**: Quick start buttons

## 📈 Usage Tracking

All components track usage and costs:

```python
# Get usage statistics
stats = pipeline.get_usage_stats()

print(f"Model: {stats['llm']['model']}")
print(f"Input tokens: {stats['llm']['total_input_tokens']:,}")
print(f"Output tokens: {stats['llm']['total_output_tokens']:,}")
print(f"Total cost: ${stats['llm']['total_cost']:.4f}")
```

## 🔍 Testing

### CLI Interactive Mode

```bash
python3 test_rag.py --mode interactive

# With filters
python3 test_rag.py --mode single \
  --query "What is encryption?" \
  --k 5 \
  --chapter 2
```

### Test Suite (10 Questions)

```bash
python3 test_rag.py --mode suite
```

Sample questions:
- What is phishing?
- Explain two-factor authentication
- What is the CIA triad?
- What are the different types of malware?
- How does encryption work?
- What is a firewall?
- Explain symmetric vs asymmetric encryption
- What is social engineering?
- What are the principles of least privilege?
- How do VPNs work?

## 🛠️ Data Pipeline

### 1. Data Cleaning

```bash
python3 data_cleaner.py
# Output: data_clean/ (112 JSON files, 701 chunks)
```

### 2. AI Summarization

```bash
python3 claude_summarizer.py
# Cost: ~$1.72 for 701 chunks
```

### 3. Embedding Generation

```bash
python3 embedding_generator_openai.py --model text-embedding-3-small
# Output: embeddings.json (32.51 MB)
# Cost: ~$0.004
```

### 4. Vector Database Upload

```bash
python3 vector_db_manager.py
# Uploads 701 vectors to Qdrant
```

## 💰 Cost Estimates

### One-time Setup Costs:
- **AI Summarization**: $1.72 (701 chunks with Claude)
- **Embeddings**: $0.004 (701 chunks with OpenAI)
- **Total Setup**: ~$1.72

### Per-Query Costs:
- **Embedding**: ~$0.00001 per query
- **Claude Answer**: ~$0.01-0.05 per answer (depends on context size)
- **Average**: ~$0.02 per Q&A

### Example Session (10 questions):
- **Total cost**: ~$0.20
- **Per question**: ~$0.02

## 🎯 Summary-Indexed Retrieval Explained

1. **Indexing Phase**:
   - Combine: `section_header + summary + content`
   - Generate embedding for combined text
   - Store: embedding, header, summary, content separately

2. **Query Phase**:
   - Generate query embedding
   - Search for similar document embeddings
   - Retrieve: header + summary + full content
   - Assemble rich context for LLM

3. **Benefits**:
   - Better semantic matching (uses summary)
   - Complete context for LLM (includes full text)
   - Source transparency (shows what was used)

## 📝 Context Format

Retrieved documents are formatted as:

```xml
<document>
Section Heading

Text:
[full original content]

Summary:
[AI-generated summary]
</document>
```

This format is then used in the LLM prompt for answer generation.

## 🔒 Security Notes

- Store API keys in `.env` (never commit to git)
- Use CORS middleware in production (restrict origins)
- Consider rate limiting for API endpoints
- Use authentication for production deployment

## 🚧 Future Enhancements

- [ ] Add evaluation metrics (accuracy, relevance)
- [ ] Implement hybrid search (keyword + semantic)
- [ ] Add conversation memory for multi-turn Q&A
- [ ] Support for more chapters (5-9)
- [ ] Fine-tune chunk sizes for optimal retrieval
- [ ] Add caching layer for common queries

## 📚 References

- **Vector DB**: Qdrant (https://qdrant.tech)
- **Embeddings**: OpenAI text-embedding-3-small
- **LLM**: Anthropic Claude Sonnet 4
- **Framework**: FastAPI + Streamlit

## 🤝 Contributing

To extend the system:

1. Add new chapters: Update `data_raw/`, run cleaning pipeline
2. Improve prompts: Edit `llm_engine.py` prompt template
3. Add features: Extend `api_server.py` or `app.py`
4. Optimize retrieval: Tune `k`, chunk sizes, or embedding strategy

---

**Built with summary-indexed RAG for faithful, source-backed CompTIA Security+ Q&A** 🔒
