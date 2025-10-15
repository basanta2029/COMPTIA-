#!/usr/bin/env python3
"""
LLM Engine for CompTIA Security+ RAG System
Handles answer generation using Gemini with enriched context
"""

import os
import re
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMEngine:
    """Gemini-powered answer generation engine"""

    def __init__(self, model: str = "gemini-2.5-pro"):
        """
        Initialize LLM engine

        Args:
            model: Gemini model to use (default: gemini-2.5-pro)
        """
        # Initialize Google Generative AI client
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables!")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.model_name = model

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0

        # Pricing (per million tokens) - Gemini 2.5 pricing
        self.pricing = {
            "gemini-2.5-pro": {"input": 1.25, "output": 10.0},
            "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-2.5-flash-8b": {"input": 0.01, "output": 0.04}
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
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )

            # Track usage
            if hasattr(response, 'usage_metadata'):
                self.total_input_tokens += response.usage_metadata.prompt_token_count
                self.total_output_tokens += response.usage_metadata.candidates_token_count

                # Calculate cost
                if self.model_name in self.pricing:
                    input_cost = (response.usage_metadata.prompt_token_count / 1_000_000) * self.pricing[self.model_name]["input"]
                    output_cost = (response.usage_metadata.candidates_token_count / 1_000_000) * self.pricing[self.model_name]["output"]
                    self.total_cost += input_cost + output_cost

            # Extract answer text
            answer = response.text

            return answer

        except Exception as e:
            print(f"❌ Error generating answer: {e}")
            raise

    def answer_exam_question(
        self,
        scenario: str,
        question: str,
        options: list,
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
            options: List of option texts (unlabeled)
            context: Retrieved context documents
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dict with {
                "answer": selected option text (full text),
                "reasoning": full chain-of-thought explanation,
                "confidence": confidence level
            }
        """
        # Format options for prompt (number them for clarity)
        options_text = "\n".join([f"{i+1}. {text}" for i, text in enumerate(options)])

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

Option 1: [Option text]
[Detailed evaluation]

Option 2: [Option text]
[Detailed evaluation]

[Continue for all options...]

**COMPARATIVE ANALYSIS:**
[Compare the options and explain trade-offs]

**BEST ANSWER:**
[Write the COMPLETE text of the best option here, verbatim]

[Final justification for why this is the MOST effective option]"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )

            # Track usage
            if hasattr(response, 'usage_metadata'):
                self.total_input_tokens += response.usage_metadata.prompt_token_count
                self.total_output_tokens += response.usage_metadata.candidates_token_count

                # Calculate cost
                if self.model_name in self.pricing:
                    input_cost = (response.usage_metadata.prompt_token_count / 1_000_000) * self.pricing[self.model_name]["input"]
                    output_cost = (response.usage_metadata.candidates_token_count / 1_000_000) * self.pricing[self.model_name]["output"]
                    self.total_cost += input_cost + output_cost

            # Extract answer text
            full_reasoning = response.text

            # Parse out the selected answer (full option text)
            selected_answer = None
            lines = full_reasoning.split('\n')

            # Find the line after "BEST ANSWER:"
            for i, line in enumerate(lines):
                if 'BEST ANSWER:' in line.upper():
                    # Check if answer is on the same line
                    answer_on_same_line = line.split('BEST ANSWER:', 1)[-1].strip()
                    if answer_on_same_line and len(answer_on_same_line) > 10:
                        selected_answer = answer_on_same_line
                    # Otherwise, get the next non-empty line
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('**'):
                            selected_answer = next_line
                    break

            # If still no answer, try to match against provided options
            if not selected_answer:
                for option in options:
                    if option.lower() in full_reasoning.lower():
                        selected_answer = option
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
            "model": self.model_name,
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
