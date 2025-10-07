#!/usr/bin/env python3
"""
FastAPI Server for CompTIA Security+ RAG System
REST API for Q&A and semantic search
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import uvicorn
from rag_pipeline import RAGPipeline, RAGResponse


# Pydantic models for request/response
class QueryRequest(BaseModel):
    """Request model for Q&A queries"""
    query: str = Field(..., description="User's question", min_length=1)
    k: int = Field(default=3, description="Number of documents to retrieve", ge=1, le=10)
    chapter_filter: Optional[str] = Field(default=None, description="Filter by chapter (e.g., '1', '2')")
    content_type_filter: Optional[str] = Field(default=None, description="Filter by content type ('video' or 'text')")
    max_tokens: int = Field(default=2500, description="Max tokens in answer", ge=100, le=4000)
    temperature: float = Field(default=0, description="LLM temperature", ge=0, le=1)


class SearchRequest(BaseModel):
    """Request model for semantic search only"""
    query: str = Field(..., description="Search query", min_length=1)
    k: int = Field(default=5, description="Number of documents to retrieve", ge=1, le=20)
    chapter_filter: Optional[str] = Field(default=None, description="Filter by chapter")
    content_type_filter: Optional[str] = Field(default=None, description="Filter by content type")


class Source(BaseModel):
    """Source document model"""
    chunk_id: str
    section_header: str
    content: str
    summary: str
    score: float
    metadata: Dict


class QueryResponse(BaseModel):
    """Response model for Q&A queries"""
    query: str
    answer: str
    sources: List[Source]
    num_sources: int
    retrieval_metadata: Dict
    llm_metadata: Dict


class SearchResponse(BaseModel):
    """Response model for semantic search"""
    query: str
    results: List[Source]
    num_results: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    collection: str
    embedding_dim: int
    llm_model: str


class ChaptersResponse(BaseModel):
    """Available chapters response"""
    chapters: List[str]
    total: int


# Initialize FastAPI app
app = FastAPI(
    title="CompTIA Security+ RAG API",
    description="REST API for CompTIA Security+ Q&A using summary-indexed RAG",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline (singleton)
pipeline: Optional[RAGPipeline] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG pipeline on startup"""
    global pipeline
    print("🚀 Initializing RAG Pipeline...")
    pipeline = RAGPipeline()
    print("✅ API Server ready")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "message": "CompTIA Security+ RAG API",
        "docs": "/docs",
        "endpoints": {
            "query": "/query",
            "search": "/search",
            "health": "/health",
            "chapters": "/chapters"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    return HealthResponse(
        status="healthy",
        collection=pipeline.retriever.vector_db.collection_name,
        embedding_dim=pipeline.retriever.vector_db.embedding_dim,
        llm_model=pipeline.llm_engine.model
    )


@app.get("/chapters", response_model=ChaptersResponse, tags=["metadata"])
async def get_chapters():
    """Get available chapters"""
    # CompTIA Security+ has chapters 1-4 in current dataset
    chapters = ["1", "2", "3", "4"]
    return ChaptersResponse(
        chapters=chapters,
        total=len(chapters)
    )


@app.post("/query", response_model=QueryResponse, tags=["rag"])
async def query_endpoint(request: QueryRequest):
    """
    Main Q&A endpoint: retrieves relevant documents and generates answer

    - **query**: User's security question
    - **k**: Number of documents to retrieve (default: 3)
    - **chapter_filter**: Optional chapter filter (e.g., "1")
    - **content_type_filter**: Optional content type filter ("video" or "text")
    - **max_tokens**: Max tokens in answer (default: 2500)
    - **temperature**: LLM temperature (default: 0 for deterministic)
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        # Run query through pipeline
        response: RAGResponse = pipeline.query(
            query=request.query,
            k=request.k,
            chapter_filter=request.chapter_filter,
            content_type_filter=request.content_type_filter,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # Convert SearchResult objects to Source models
        sources = [
            Source(
                chunk_id=src.chunk_id,
                section_header=src.section_header,
                content=src.content,
                summary=src.summary,
                score=src.score,
                metadata=src.metadata
            )
            for src in response.sources
        ]

        return QueryResponse(
            query=response.query,
            answer=response.answer,
            sources=sources,
            num_sources=response.num_sources,
            retrieval_metadata=response.retrieval_metadata,
            llm_metadata=response.llm_metadata
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.post("/search", response_model=SearchResponse, tags=["search"])
async def search_endpoint(request: SearchRequest):
    """
    Semantic search endpoint: retrieves relevant documents without LLM generation

    - **query**: Search query
    - **k**: Number of documents to retrieve (default: 5)
    - **chapter_filter**: Optional chapter filter
    - **content_type_filter**: Optional content type filter
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    try:
        # Retrieve documents only (no LLM)
        results, _ = pipeline.retriever.retrieve_level_two(
            query=request.query,
            k=request.k,
            chapter_filter=request.chapter_filter,
            content_type_filter=request.content_type_filter
        )

        # Convert to Source models
        sources = [
            Source(
                chunk_id=src.chunk_id,
                section_header=src.section_header,
                content=src.content,
                summary=src.summary,
                score=src.score,
                metadata=src.metadata
            )
            for src in results
        ]

        return SearchResponse(
            query=request.query,
            results=sources,
            num_results=len(sources)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/stats", tags=["system"])
async def get_stats():
    """Get usage statistics"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")

    return pipeline.get_usage_stats()


def main():
    """Run the API server"""
    import argparse

    parser = argparse.ArgumentParser(description="Run CompTIA Security+ RAG API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    print("=" * 60)
    print("STARTING COMPTIA SECURITY+ RAG API SERVER")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Docs: http://{args.host}:{args.port}/docs")
    print("=" * 60)

    uvicorn.run(
        "api_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
