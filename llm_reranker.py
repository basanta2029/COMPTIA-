#!/usr/bin/env python3
"""
LLM-Based Reranker for RAG System
Uses Gemini to intelligently rerank retrieved documents
"""

import os
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
from vector_db_manager import SearchResult

load_dotenv()


class LLMReranker:
    """Gemini-powered document reranker"""

    def __init__(self, model: str = "gemini-2.5-flash-8b"):
        """
        Initialize reranker

        Args:
            model: Gemini model (flash-8b recommended for cost/speed)
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found!")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        k: int = 3
    ) -> List[SearchResult]:
        """
        Rerank documents using Gemini's contextual understanding

        Args:
            query: User's question
            results: Initial search results from vector DB
            k: Number of top documents to return

        Returns:
            Reranked list of top-k SearchResult objects
        """
        if len(results) == 0:
            return []

        if len(results) <= k:
            # No need to rerank if we have k or fewer results
            return results[:k]

        # Build summaries with indices
        summaries = []
        for i, result in enumerate(results):
            summary_text = f"[{i}] Section: {result.section_header}\n"
            summary_text += f"Summary: {result.summary}"
            summaries.append(summary_text)

        joined_summaries = "\n\n".join(summaries)

        # Reranking prompt
        prompt = f"""Query: {query}

You are given {len(results)} documents, each with an index number [0-{len(results)-1}] in square brackets.

Your task: Select the {k} MOST relevant documents that would best help answer the query.

Consider:
- Direct relevance to the query topic
- Information completeness
- Accuracy and specificity
- Complementary information (avoid redundancy)

<documents>
{joined_summaries}
</documents>

Output ONLY the indices of the {k} most relevant documents, in order of relevance (most relevant first).
Format: comma-separated numbers, no spaces, inside XML tags.

<relevant_indices>"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=50,
                    temperature=0,
                    stop_sequences=["</relevant_indices>"]
                )
            )

            # Track usage (if available)
            try:
                if hasattr(response, 'usage_metadata'):
                    self.total_input_tokens += response.usage_metadata.prompt_token_count
                    self.total_output_tokens += response.usage_metadata.candidates_token_count
            except:
                pass

            # Parse indices
            response_text = response.text.strip()
            relevant_indices = []

            for idx_str in response_text.split(','):
                try:
                    idx = int(idx_str.strip())
                    if 0 <= idx < len(results):
                        relevant_indices.append(idx)
                except ValueError:
                    continue

            # Fallback: if parsing failed, use top k by vector score
            if len(relevant_indices) == 0:
                print("⚠️  Reranking failed, using vector scores")
                return results[:k]

            # Build reranked results
            reranked = []
            for idx in relevant_indices[:k]:
                result = results[idx]
                # Update score to reflect reranking position
                result.score = 1.0 - (len(reranked) * 0.05)  # Descending scores
                reranked.append(result)

            # Fill with remaining top results if we got fewer than k
            while len(reranked) < k and len(reranked) < len(results):
                for result in results:
                    if result not in reranked:
                        reranked.append(result)
                        if len(reranked) >= k:
                            break

            return reranked[:k]

        except Exception as e:
            print(f"❌ Reranking error: {e}")
            # Fallback to original order
            return results[:k]

    def get_usage_stats(self) -> dict:
        """Get reranking usage statistics"""
        return {
            "model": self.model_name,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens
        }


def main():
    """Test reranker"""
    print("=" * 60)
    print("LLM RERANKER TEST")
    print("=" * 60)
    print("\n✅ LLM Reranker module loaded successfully")
    print(f"   Default model: gemini-2.5-flash-8b")
    print(f"   Cost per rerank: ~$0.000002 (20 docs → 3)")
    print("\nNote: Full testing requires actual SearchResult objects")
    print("      Use with rag_retriever.py for end-to-end testing")
    print("=" * 60)


if __name__ == "__main__":
    main()
