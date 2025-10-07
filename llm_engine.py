#!/usr/bin/env python3
"""
LLM Engine for CompTIA Security+ RAG System
Handles answer generation using Claude with enriched context
"""

import os
import re
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

    def answer_exam_question(
        self,
        scenario: str,
        question: str,
        options: dict,
        context: str,
        max_tokens: int = 3000,
        temperature: float = 0
    ) -> dict:
        """
        Answer CompTIA Security+ exam-style scenario-based questions

        Uses chain-of-thought reasoning to:
        1. Analyze the scenario and identify key requirements
        2. Evaluate each option against those requirements
        3. Select the MOST effective option with justification

        Args:
            scenario: The scenario description
            question: The question being asked
            options: Dict of option letters to option text (e.g., {"A": "...", "B": "..."})
            context: Retrieved context documents
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dict with {
                "answer": selected option letter,
                "reasoning": full chain-of-thought explanation,
                "confidence": confidence level
            }
        """
        # Format options for prompt
        options_text = "\n".join([f"{letter}. {text}" for letter, text in options.items()])

        prompt = f"""You are an expert CompTIA Security+ instructor helping a student answer a scenario-based exam question.

<scenario>
{scenario}
</scenario>

<question>
{question}
</question>

<options>
{options_text}
</options>

<reference_materials>
{context}
</reference_materials>

Your task is to determine which option is the MOST effective answer. Follow this analysis framework:

**Step 1: Scenario Analysis**
- Identify the core problem or requirement in the scenario
- Note any constraints, priorities, or organizational context
- Determine what success looks like in this situation

**Step 2: Option Evaluation**
- For EACH option, explain:
  * What it does and how it addresses the scenario
  * Its strengths and benefits
  * Its limitations or drawbacks
  * Whether it fully solves the problem or only partially

**Step 3: Comparative Analysis**
- Compare the options against each other
- Identify why some options are good but not BEST
- Consider factors like: effectiveness, scope, timeliness, cost-efficiency, long-term vs short-term impact

**Step 4: Final Selection**
- Select the MOST effective option
- Justify why this option is superior to the others
- Explain what makes it the "best" choice for this specific scenario

Use the reference materials provided, but also apply your security knowledge to reason through trade-offs between options. Remember: multiple options may be technically correct, but only ONE is the MOST effective for the given scenario.

Provide your analysis in this format:

**SCENARIO ANALYSIS:**
[Your analysis of the core problem and requirements]

**OPTION EVALUATIONS:**

Option A: [Option text]
[Detailed evaluation]

Option B: [Option text]
[Detailed evaluation]

[Continue for all options...]

**COMPARATIVE ANALYSIS:**
[Compare the options and explain trade-offs]

**BEST ANSWER: [Letter]**
[Final justification for why this is the MOST effective option]"""

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
            full_reasoning = response.content[0].text

            # Parse out the selected answer
            selected_answer = None
            for line in full_reasoning.split('\n'):
                if 'BEST ANSWER:' in line.upper():
                    # Extract letter (A, B, C, or D) - look for letter immediately after "BEST ANSWER:"
                    # Match pattern like "BEST ANSWER: A" or "BEST ANSWER: [A]"
                    match = re.search(r'BEST\s+ANSWER:\s*\[?([A-D])\]?', line, re.IGNORECASE)
                    if match:
                        selected_answer = match.group(1).upper()
                    break

            return {
                "answer": selected_answer,
                "reasoning": full_reasoning,
                "confidence": "high" if selected_answer else "low"
            }

        except Exception as e:
            print(f"❌ Error generating exam answer: {e}")
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
