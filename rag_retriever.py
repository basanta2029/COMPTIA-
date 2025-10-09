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
        model: str = "text-embedding-3-small",
        auto_load_embeddings: bool = True
    ):
        """
        Initialize RAG retriever

        Args:
            collection_name: Qdrant collection name
            embedding_dim: Embedding dimension (1536 for text-embedding-3-small)
            model: OpenAI embedding model
            auto_load_embeddings: Auto-load embeddings if in-memory mode detected
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

        # Check if collection exists, if not and auto_load is enabled, load embeddings
        if auto_load_embeddings:
            try:
                collections = self.vector_db.client.get_collections().collections
                collection_exists = any(c.name == collection_name for c in collections)

                if not collection_exists:
                    embeddings_file = "embeddings.json"
                    if os.path.exists(embeddings_file):
                        print(f"📥 Collection not found. Auto-loading embeddings from {embeddings_file}...")
                        try:
                            self.vector_db.create_collection(recreate=False)
                            count = self.vector_db.upload_embeddings(embeddings_file)
                            print(f"✅ Loaded {count} embeddings into collection")
                        except Exception as e:
                            print(f"⚠️  Error loading embeddings: {e}")
                    else:
                        print(f"⚠️  Collection not found and {embeddings_file} does not exist")
            except Exception as e:
                print(f"⚠️  Error checking collection status: {e}")

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

    def retrieve_for_exam_question(
        self,
        scenario: str,
        question: str,
        options: list,
        k: int = 7,
        chapter_filter: Optional[str] = None
    ) -> Tuple[List[SearchResult], str]:
        """
        Enhanced retrieval for exam-style scenario questions

        Uses query expansion to retrieve context for:
        1. The scenario itself
        2. The specific question
        3. Each answer option individually

        Then deduplicates and assembles comprehensive context

        Args:
            scenario: The scenario description
            question: The question being asked
            options: List of option texts (unlabeled)
            k: Number of documents per query expansion
            chapter_filter: Optional chapter filter

        Returns:
            Tuple of (deduplicated_results, formatted_context)
        """
        # Collect all unique results by chunk_id
        results_by_id = {}

        # Query 1: Scenario + Question combined
        main_query = f"{scenario} {question}"
        main_results, _ = self.retrieve_level_two(
            query=main_query,
            k=k,
            chapter_filter=chapter_filter
        )
        for result in main_results:
            results_by_id[result.chunk_id] = result

        # Query 2-N: Each answer option
        for option_text in options:
            # Combine scenario context with option for better relevance
            option_query = f"{question} {option_text}"
            option_results, _ = self.retrieve_level_two(
                query=option_query,
                k=max(3, k // 2),  # Fewer docs per option
                chapter_filter=chapter_filter
            )
            for result in option_results:
                if result.chunk_id not in results_by_id:
                    results_by_id[result.chunk_id] = result

        # Convert to list and sort by best average relevance
        unique_results = list(results_by_id.values())

        # Sort by score (highest first)
        unique_results.sort(key=lambda x: x.score, reverse=True)

        # Take top results (limit to avoid context overflow)
        final_results = unique_results[:min(12, len(unique_results))]

        # Assemble context
        context = ""
        for result in final_results:
            context += "\n<document>\n"
            context += f"{result.section_header}\n\n"
            context += f"Text:\n{result.content}\n\n"
            context += f"Summary:\n{result.summary}\n"
            context += "</document>\n"

        return final_results, context

    def retrieve_with_reranking(
        self,
        query: str,
        k: int = 3,
        initial_k: int = 40,  # Increased from 20 for better coverage with 2321 chunks
        chapter_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None,
        reranker_model: str = "claude-3-5-sonnet-20241022"  # Upgraded from Haiku for better accuracy
    ) -> Tuple[List[SearchResult], str]:
        """
        Two-stage retrieval with LLM-based reranking

        Stage 1: Retrieve initial_k candidates from vector DB (e.g., 20)
        Stage 2: Use Claude LLM to rerank and select top-k most relevant (e.g., 3)

        Args:
            query: User's question
            k: Number of final documents to return (after reranking)
            initial_k: Number of initial candidates to retrieve
            chapter_filter: Optional chapter number (e.g., "1", "2")
            content_type_filter: Optional content type ("video" or "text")
            reranker_model: Claude model for reranking (default: Haiku for cost)

        Returns:
            Tuple of (reranked_results, formatted_context)
        """
        from llm_reranker import LLMReranker

        # Stage 1: Retrieve initial candidates
        query_vector = self.embed_query(query)
        initial_results = self.vector_db.search(
            query_vector=query_vector,
            top_k=initial_k,
            chapter_filter=chapter_filter,
            content_type_filter=content_type_filter
        )

        if len(initial_results) == 0:
            return [], ""

        # Stage 2: LLM-based reranking
        reranker = LLMReranker(model=reranker_model)
        reranked_results = reranker.rerank(
            query=query,
            results=initial_results,
            k=k
        )

        # Assemble context from reranked results
        context = ""
        for result in reranked_results:
            context += "\n<document>\n"
            context += f"{result.section_header}\n\n"
            context += f"Text:\n{result.content}\n\n"
            context += f"Summary:\n{result.summary}\n"
            context += "</document>\n"

        return reranked_results, context


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
