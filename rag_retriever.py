#!/usr/bin/env python3
"""
RAG Retriever for CompTIA Security+ System
Handles query embedding and Qdrant vector search with context assembly
"""

import os
from typing import List, Dict, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from vector_db_manager import VectorDBManager, SearchResult

# Load environment variables
load_dotenv()


class RAGRetriever:
    """Retrieval system for summary-indexed RAG"""

    def __init__(
        self,
        collection_name: str = "comptia_security_plus",
        embedding_dim: int = 1536,
        model: str = "text-embedding-3-small"
    ):
        """
        Initialize RAG retriever

        Args:
            collection_name: Qdrant collection name
            embedding_dim: Embedding dimension (1536 for text-embedding-3-small)
            model: OpenAI embedding model
        """
        # Initialize OpenAI for query embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables!")

        self.client = OpenAI(api_key=api_key)
        self.model = model

        # Initialize Qdrant vector database
        self.vector_db = VectorDBManager(
            collection_name=collection_name,
            embedding_dim=embedding_dim
        )

        print(f"✅ RAG Retriever initialized")
        print(f"   Model: {model}")
        print(f"   Embedding dim: {embedding_dim}")
        print(f"   Collection: {collection_name}")

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for user query

        Args:
            query: User's question

        Returns:
            Embedding vector (1536 dimensions)
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[query]
            )
            return response.data[0].embedding

        except Exception as e:
            print(f"❌ Error generating query embedding: {e}")
            raise

    def retrieve_level_two(
        self,
        query: str,
        k: int = 3,
        chapter_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None
    ) -> Tuple[List[SearchResult], str]:
        """
        Summary-indexed retrieval (Level 2)

        Retrieves top-k documents and assembles context with:
        - Section heading
        - Full text content
        - AI-generated summary

        Args:
            query: User's question
            k: Number of documents to retrieve
            chapter_filter: Optional chapter number (e.g., "1", "2")
            content_type_filter: Optional content type ("video" or "text")

        Returns:
            Tuple of (search_results, formatted_context)
        """
        # 1. Generate query embedding
        query_vector = self.embed_query(query)

        # 2. Search Qdrant
        results = self.vector_db.search(
            query_vector=query_vector,
            top_k=k,
            chapter_filter=chapter_filter,
            content_type_filter=content_type_filter
        )

        # 3. Assemble context (format matches your sample code)
        context = ""
        for result in results:
            context += "\n<document>\n"
            context += f"{result.section_header}\n\n"
            context += f"Text:\n{result.content}\n\n"
            context += f"Summary:\n{result.summary}\n"
            context += "</document>\n"

        return results, context

    def retrieve_with_scores(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Retrieve documents with detailed scoring

        Args:
            query: User's question
            k: Number of documents to retrieve
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of dictionaries with full document info + scores
        """
        query_vector = self.embed_query(query)
        results = self.vector_db.search(query_vector=query_vector, top_k=k)

        # Filter by score and return detailed results
        detailed_results = []
        for result in results:
            if result.score >= score_threshold:
                detailed_results.append({
                    "chunk_id": result.chunk_id,
                    "section_header": result.section_header,
                    "content": result.content,
                    "summary": result.summary,
                    "score": result.score,
                    "metadata": result.metadata
                })

        return detailed_results


def main():
    """Test the retriever with sample queries"""
    print("=" * 60)
    print("RAG RETRIEVER TEST")
    print("=" * 60)

    # Initialize retriever
    retriever = RAGRetriever()

    # Test queries
    test_queries = [
        "What is phishing?",
        "Explain two-factor authentication",
        "What is the CIA triad?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")

        # Retrieve documents
        results, context = retriever.retrieve_level_two(query, k=3)

        print(f"\n📊 Retrieved {len(results)} documents:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result.chunk_id}] {result.section_header}")
            print(f"   Score: {result.score:.4f}")
            print(f"   Chapter: {result.metadata.get('chapter_num')}")
            print(f"   Summary: {result.summary[:100]}...")

        print(f"\n📄 Context length: {len(context)} characters")
        print(f"\n🔍 Context preview:")
        print(context[:500] + "...")


if __name__ == "__main__":
    main()
