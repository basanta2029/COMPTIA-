#!/usr/bin/env python3
"""
LLM Engine for CompTIA Security+ RAG System
Handles answer generation using Claude with enriched context
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMEngine:
    """Claude-powered answer generation engine"""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize LLM engine

        Args:
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables!")

        self.client = Anthropic(api_key=api_key)
        self.model = model

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        # Pricing (per million tokens)
        # Claude Sonnet 4: $3 input / $15 output per million tokens
        self.pricing = {
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25}
        }

        print(f"✅ LLM Engine initialized")
        print(f"   Model: {model}")

    def answer_query_level_two(
        self,
        query: str,
        context: str,
        max_tokens: int = 2500,
        temperature: float = 0
    ) -> str:
        """
        Generate answer using summary-indexed retrieval context

        Args:
            query: User's question
            context: Formatted context string from retriever (with <document> tags)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0 for deterministic)

        Returns:
            Generated answer text
        """
        # Build prompt using user's exact template
        prompt = f"""You have been tasked with helping us to answer the following query:
<query>
{query}
</query>

You have access to the following documents which are meant to provide context as you answer the query:
<documents>
{context}
</documents>

Please remain faithful to the underlying context, and only deviate from it if you are 100% sure that you know the answer already.
Answer the question now, and avoid providing preamble such as 'Here is the answer', etc"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )

            # Track usage
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens

            # Calculate cost
            if self.model in self.pricing:
                input_cost = (response.usage.input_tokens / 1_000_000) * self.pricing[self.model]["input"]
                output_cost = (response.usage.output_tokens / 1_000_000) * self.pricing[self.model]["output"]
                self.total_cost += input_cost + output_cost

            # Extract answer text
            answer = response.content[0].text

            return answer

        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            raise

    def get_usage_stats(self) -> dict:
        """Get usage statistics"""
        return {
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost": round(self.total_cost, 4)
        }


def main():
    """Test the LLM engine with sample context"""
    print("=" * 60)
    print("LLM ENGINE TEST")
    print("=" * 60)

    # Initialize engine
    engine = LLMEngine()

    # Sample query
    query = "What is phishing?"

    # Sample context (simulating retriever output)
    context = """
<document>
Phishing Attacks

Text:
Phishing is a social engineering attack where attackers send fraudulent communications that appear to come from a reputable source. The goal is to steal sensitive data like login credentials or credit card numbers. Phishing attacks are typically delivered via email but can also occur through text messages (smishing) or phone calls (vishing).

Summary:
Phishing is a social engineering technique using fraudulent communications to steal sensitive information like credentials and financial data, commonly delivered via email, text, or phone.
</document>

<document>
Types of Phishing

Text:
Spear phishing targets specific individuals or organizations with customized messages. Whaling attacks target high-profile individuals like executives. Clone phishing duplicates legitimate emails but replaces links with malicious ones. These targeted approaches are more sophisticated than generic phishing campaigns.

Summary:
Advanced phishing variants include spear phishing (targeted individuals), whaling (executives), and clone phishing (duplicated legitimate emails), all more sophisticated than generic campaigns.
</document>
"""

    print(f"\nQuery: {query}")
    print(f"\nContext length: {len(context)} characters")
    print(f"\n{'='*60}")
    print("Generating answer...")
    print(f"{'='*60}\n")

    # Generate answer
    answer = engine.answer_query_level_two(query, context)

    print("ANSWER:")
    print("-" * 60)
    print(answer)
    print("-" * 60)

    # Print usage stats
    stats = engine.get_usage_stats()
    print(f"\n📊 Usage Statistics:")
    print(f"   Model: {stats['model']}")
    print(f"   Input tokens: {stats['total_input_tokens']:,}")
    print(f"   Output tokens: {stats['total_output_tokens']:,}")
    print(f"   Total cost: ${stats['total_cost']:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
