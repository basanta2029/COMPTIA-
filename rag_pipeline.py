#!/usr/bin/env python3
"""
Complete RAG Pipeline for CompTIA Security+ System
Combines retrieval and answer generation into unified Q&A system
"""

import os
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from rag_retriever import RAGRetriever, SearchResult
from llm_engine import LLMEngine

# Load environment variables
load_dotenv()


@dataclass
class RAGResponse:
    """Complete RAG response with answer and sources"""
    query: str
    answer: str
    sources: List[SearchResult]
    num_sources: int
    retrieval_metadata: Dict
    llm_metadata: Dict


class RAGPipeline:
    """Complete RAG pipeline combining retrieval + LLM"""

    def __init__(
        self,
        collection_name: str = "comptia_security_plus",
        embedding_dim: int = 1536,
        embedding_model: str = "text-embedding-3-small",
        llm_model: str = "claude-sonnet-4-20250514"
    ):
        """
        Initialize complete RAG pipeline

        Args:
            collection_name: Qdrant collection name
            embedding_dim: Embedding dimension
            embedding_model: OpenAI embedding model
            llm_model: Claude model for answer generation
        """
        print("=" * 60)
        print("INITIALIZING RAG PIPELINE")
        print("=" * 60)

        # Initialize retriever
        self.retriever = RAGRetriever(
            collection_name=collection_name,
            embedding_dim=embedding_dim,
            model=embedding_model
        )

        # Initialize LLM engine
        self.llm_engine = LLMEngine(model=llm_model)

        print("=" * 60)
        print("✅ RAG Pipeline ready")
        print("=" * 60)

    def query(
        self,
        query: str,
        k: int = 3,
        chapter_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        max_tokens: int = 2500,
        temperature: float = 0
    ) -> RAGResponse:
        """
        Complete Q&A pipeline: retrieve → generate answer

        Args:
            query: User's question
            k: Number of documents to retrieve
            chapter_filter: Optional chapter filter (e.g., "1", "2")
            content_type_filter: Optional content type filter ("video" or "text")
            max_tokens: Max tokens in answer
            temperature: LLM sampling temperature

        Returns:
            RAGResponse with answer and source documents
        """
        print(f"\n{'='*60}")
        print(f"QUERY: {query}")
        print(f"{'='*60}")

        # Step 1: Retrieve documents
        print(f"\n🔍 Retrieving top-{k} documents...")
        if chapter_filter:
            print(f"   Filter: Chapter {chapter_filter}")
        if content_type_filter:
            print(f"   Filter: Content type '{content_type_filter}'")

        results, context = self.retriever.retrieve_level_two(
            query=query,
            k=k,
            chapter_filter=chapter_filter,
            content_type_filter=content_type_filter
        )

        print(f"✅ Retrieved {len(results)} documents")
        print(f"   Context length: {len(context):,} characters")

        # Step 2: Generate answer
        print(f"\n🤖 Generating answer with {self.llm_engine.model}...")

        answer = self.llm_engine.answer_query_level_two(
            query=query,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature
        )

        print(f"✅ Answer generated ({len(answer)} characters)")

        # Build response
        response = RAGResponse(
            query=query,
            answer=answer,
            sources=results,
            num_sources=len(results),
            retrieval_metadata={
                "k": k,
                "chapter_filter": chapter_filter,
                "content_type_filter": content_type_filter,
                "context_length": len(context)
            },
            llm_metadata={
                "model": self.llm_engine.model,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )

        return response

    def query_with_reranking(
        self,
        query: str,
        k: int = 3,
        initial_k: int = 20,
        chapter_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        reranker_model: str = "claude-3-haiku-20240307",
        max_tokens: int = 2500,
        temperature: float = 0
    ) -> RAGResponse:
        """
        Complete Q&A pipeline with LLM-based reranking

        Two-stage retrieval:
        1. Retrieve initial_k candidates from vector DB (e.g., 20)
        2. Use Claude to rerank and select top-k most relevant (e.g., 3)
        3. Generate answer from reranked documents

        Args:
            query: User's question
            k: Number of final documents to use (after reranking)
            initial_k: Number of initial candidates to retrieve
            chapter_filter: Optional chapter filter (e.g., "1", "2")
            content_type_filter: Optional content type filter ("video" or "text")
            reranker_model: Claude model for reranking (default: Haiku)
            max_tokens: Max tokens in answer
            temperature: LLM sampling temperature

        Returns:
            RAGResponse with answer and reranked source documents
        """
        print(f"\n{'='*60}")
        print(f"QUERY (with reranking): {query}")
        print(f"{'='*60}")

        # Step 1: Two-stage retrieval with reranking
        print(f"\n🔍 Stage 1: Retrieving {initial_k} candidates...")
        if chapter_filter:
            print(f"   Filter: Chapter {chapter_filter}")
        if content_type_filter:
            print(f"   Filter: Content type '{content_type_filter}'")

        results, context = self.retriever.retrieve_with_reranking(
            query=query,
            k=k,
            initial_k=initial_k,
            chapter_filter=chapter_filter,
            content_type_filter=content_type_filter,
            reranker_model=reranker_model
        )

        print(f"🔄 Stage 2: Reranked to top-{k} documents")
        print(f"✅ Final context: {len(context):,} characters")

        # Step 2: Generate answer
        print(f"\n🤖 Generating answer with {self.llm_engine.model}...")

        answer = self.llm_engine.answer_query_level_two(
            query=query,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature
        )

        print(f"✅ Answer generated ({len(answer)} characters)")

        # Build response
        response = RAGResponse(
            query=query,
            answer=answer,
            sources=results,
            num_sources=len(results),
            retrieval_metadata={
                "k": k,
                "initial_k": initial_k,
                "reranker_model": reranker_model,
                "chapter_filter": chapter_filter,
                "content_type_filter": content_type_filter,
                "context_length": len(context)
            },
            llm_metadata={
                "model": self.llm_engine.model,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
        )

        return response

    def get_usage_stats(self) -> Dict:
        """Get combined usage statistics"""
        llm_stats = self.llm_engine.get_usage_stats()

        return {
            "retrieval": {
                "embedding_model": self.retriever.model,
                "collection": self.retriever.vector_db.collection_name,
                "embedding_dim": self.retriever.vector_db.embedding_dim
            },
            "llm": llm_stats
        }

    def display_response(self, response: RAGResponse) -> None:
        """Pretty-print RAG response"""
        print(f"\n{'='*60}")
        print("ANSWER")
        print(f"{'='*60}")
        print(response.answer)
        print(f"{'='*60}")

        print(f"\n📚 Sources ({response.num_sources} documents):")
        print(f"{'-'*60}")
        for i, source in enumerate(response.sources, 1):
            print(f"\n{i}. {source.section_header}")
            print(f"   Chunk ID: {source.chunk_id}")
            print(f"   Score: {source.score:.4f}")
            print(f"   Chapter: {source.metadata.get('chapter_num')}")
            print(f"   Type: {source.metadata.get('content_type')}")
            print(f"   Summary: {source.summary[:100]}...")

        print(f"\n{'-'*60}")
        print(f"📊 Retrieval: k={response.retrieval_metadata['k']}, context={response.retrieval_metadata['context_length']:,} chars")
        print(f"🤖 LLM: {response.llm_metadata['model']}, temp={response.llm_metadata['temperature']}")
        print(f"{'='*60}")


def main():
    """Test the complete RAG pipeline"""
    print("\n" + "=" * 60)
    print("RAG PIPELINE TEST")
    print("=" * 60)

    # Initialize pipeline
    pipeline = RAGPipeline()

    # Test queries
    test_queries = [
        "What is phishing?",
        "Explain two-factor authentication",
        "What is the CIA triad?"
    ]

    for query in test_queries:
        # Run query
        response = pipeline.query(query, k=3)

        # Display results
        pipeline.display_response(response)

        print("\n" + "=" * 60)
        input("Press Enter to continue to next query...")
        print()

    # Print final usage stats
    stats = pipeline.get_usage_stats()
    print("\n" + "=" * 60)
    print("FINAL USAGE STATISTICS")
    print("=" * 60)
    print(f"Retrieval model: {stats['retrieval']['embedding_model']}")
    print(f"LLM model: {stats['llm']['model']}")
    print(f"Total input tokens: {stats['llm']['total_input_tokens']:,}")
    print(f"Total output tokens: {stats['llm']['total_output_tokens']:,}")
    print(f"Total cost: ${stats['llm']['total_cost']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
