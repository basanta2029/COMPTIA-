#!/usr/bin/env python3
"""
LLM-Based Reranker for RAG System
Uses Claude to intelligently rerank retrieved documents
"""

import os
from typing import List
from anthropic import Anthropic
from dotenv import load_dotenv
from vector_db_manager import SearchResult

load_dotenv()


class LLMReranker:
    """Claude-powered document reranker"""

    def __init__(self, model: str = "claude-3-haiku-20240307"):
        """
        Initialize reranker

        Args:
            model: Claude model (haiku recommended for cost/speed)
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found!")

        self.client = Anthropic(api_key=api_key)
        self.model = model

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
        Rerank documents using Claude's contextual understanding

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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": "<relevant_indices>"}
                ],
                temperature=0,
                stop_sequences=["</relevant_indices>"]
            )

            # Track usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            # Parse indices
            response_text = response.content[0].text.strip()
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
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens
        }


def main():
    """Test reranker"""
    print("=" * 60)
    print("LLM RERANKER TEST")
    print("=" * 60)
    print("\n✅ LLM Reranker module loaded successfully")
    print(f"   Default model: claude-3-haiku-20240307")
    print(f"   Cost per rerank: ~$0.0003 (20 docs → 3)")
    print("\nNote: Full testing requires actual SearchResult objects")
    print("      Use with rag_retriever.py for end-to-end testing")
    print("=" * 60)


if __name__ == "__main__":
    main()
