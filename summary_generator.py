#!/usr/bin/env python3
"""
Summary Generator for CompTIA Security+ RAG System
Generates concise summaries for all chunks using OpenAI GPT-4o-mini
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class SummaryGenerator:
    """Generate summaries for content chunks using OpenAI"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize summary generator

        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4o-mini for cost-effectiveness)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

        # Usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.successful_summaries = 0
        self.failed_summaries = 0

        # Pricing (per million tokens) for gpt-4o-mini
        self.pricing = {
            "gpt-4o-mini": {
                "input": 0.150,   # $0.150 per 1M tokens
                "output": 0.600   # $0.600 per 1M tokens
            },
            "gpt-4o": {
                "input": 2.50,
                "output": 10.00
            }
        }

    def create_summary_prompt(self, chunk: Dict) -> str:
        """
        Create prompt for summarization

        Args:
            chunk: Chunk dictionary with content and section_header

        Returns:
            Prompt string
        """
        section_header = chunk.get('section_header', 'General')
        content = chunk.get('content', '')

        prompt = f"""Summarize the following CompTIA Security+ course content in 2-3 sentences.
Focus on the key security concepts, main topics, and practical applications.
Be concise but informative.

Section: {section_header}

Content:
{content}

Summary (2-3 sentences):"""

        return prompt

    def generate_summary(self, chunk: Dict, retries: int = 3) -> Optional[str]:
        """
        Generate summary for a single chunk

        Args:
            chunk: Chunk dictionary
            retries: Number of retry attempts

        Returns:
            Summary string or None if failed
        """
        prompt = self.create_summary_prompt(chunk)

        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert at summarizing cybersecurity educational content. Create concise, informative summaries."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=150,
                    temperature=0.3  # Lower temperature for more consistent summaries
                )

                # Extract summary
                summary = response.choices[0].message.content.strip()

                # Track usage
                self.total_input_tokens += response.usage.prompt_tokens
                self.total_output_tokens += response.usage.completion_tokens

                # Calculate cost
                pricing = self.pricing.get(self.model, self.pricing["gpt-4o-mini"])
                input_cost = (response.usage.prompt_tokens / 1_000_000) * pricing["input"]
                output_cost = (response.usage.completion_tokens / 1_000_000) * pricing["output"]
                self.total_cost += (input_cost + output_cost)

                self.successful_summaries += 1
                return summary

            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    print(f"\n❌ Error generating summary after {retries} attempts: {e}")
                    self.failed_summaries += 1
                    return None

        return None

    def generate_batch_summaries(self, chunks: List[Dict], delay: float = 0.1) -> List[Dict]:
        """
        Generate summaries for a batch of chunks

        Args:
            chunks: List of chunk dictionaries
            delay: Delay between requests (seconds)

        Returns:
            Updated chunks with summaries
        """
        updated_chunks = []

        for chunk in tqdm(chunks, desc="Generating summaries", leave=False):
            # Skip if already has summary
            if chunk.get('summary') and chunk['summary'].strip():
                updated_chunks.append(chunk)
                continue

            # Generate summary
            summary = self.generate_summary(chunk)

            # Update chunk
            chunk['summary'] = summary if summary else ""
            updated_chunks.append(chunk)

            # Rate limiting
            time.sleep(delay)

        return updated_chunks

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "model": self.model,
            "successful_summaries": self.successful_summaries,
            "failed_summaries": self.failed_summaries,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": round(self.total_cost, 4)
        }


class ChunkSummarizer:
    """Main pipeline for summarizing all chunks"""

    def __init__(self, data_dir: str = "data_clean"):
        """
        Initialize chunk summarizer

        Args:
            data_dir: Directory containing cleaned JSON files
        """
        self.data_dir = Path(data_dir)
        self.stats = {
            'total_files': 0,
            'files_processed': 0,
            'total_chunks': 0,
            'chunks_summarized': 0,
            'chunks_skipped': 0
        }

    def find_json_files(self) -> List[Path]:
        """
        Find all JSON files to process

        Returns:
            List of JSON file paths
        """
        json_files = []
        for json_file in self.data_dir.rglob("*.json"):
            # Skip overview and report files
            if json_file.name not in ['chapter_overview.json', 'validation_report.json',
                                      'ai_summary_report.json', 'embeddings.json']:
                json_files.append(json_file)

        return sorted(json_files)

    def process_file(self, file_path: Path, generator: SummaryGenerator) -> bool:
        """
        Process a single JSON file

        Args:
            file_path: Path to JSON file
            generator: SummaryGenerator instance

        Returns:
            True if successful, False otherwise
        """
        try:
            # Load file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get chunks
            chunks = data.get('chunks', [])
            if not chunks:
                return True  # Skip files without chunks

            self.stats['total_chunks'] += len(chunks)

            # Generate summaries
            updated_chunks = generator.generate_batch_summaries(chunks)

            # Count summaries
            for chunk in updated_chunks:
                if chunk.get('summary') and chunk['summary'].strip():
                    self.stats['chunks_summarized'] += 1
                else:
                    self.stats['chunks_skipped'] += 1

            # Update data
            data['chunks'] = updated_chunks

            # Save back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.stats['files_processed'] += 1
            return True

        except Exception as e:
            print(f"\n❌ Error processing {file_path.name}: {e}")
            return False

    def run(self, api_key: str, model: str = "gpt-4o-mini") -> Dict:
        """
        Run the full summarization pipeline

        Args:
            api_key: OpenAI API key
            model: Model to use

        Returns:
            Statistics dictionary
        """
        print("=" * 70)
        print("SUMMARY GENERATION - CompTIA Security+ RAG System")
        print("=" * 70)

        # Initialize generator
        generator = SummaryGenerator(api_key=api_key, model=model)
        print(f"\n📝 Using model: {model}")

        # Find files
        json_files = self.find_json_files()
        self.stats['total_files'] = len(json_files)
        print(f"📂 Found {len(json_files)} JSON files to process")

        # Process files
        print("\n🔄 Processing files...")
        for file_path in tqdm(json_files, desc="Files"):
            self.process_file(file_path, generator)

        # Get usage stats
        usage_stats = generator.get_usage_stats()

        # Print results
        print("\n" + "=" * 70)
        print("PROCESSING COMPLETE")
        print("=" * 70)
        print(f"Files processed: {self.stats['files_processed']}/{self.stats['total_files']}")
        print(f"Total chunks: {self.stats['total_chunks']}")
        print(f"Chunks summarized: {self.stats['chunks_summarized']}")
        print(f"Chunks skipped: {self.stats['chunks_skipped']}")

        print("\n" + "=" * 70)
        print("USAGE STATISTICS")
        print("=" * 70)
        print(f"Model: {usage_stats['model']}")
        print(f"Successful summaries: {usage_stats['successful_summaries']}")
        print(f"Failed summaries: {usage_stats['failed_summaries']}")
        print(f"Input tokens: {usage_stats['total_input_tokens']:,}")
        print(f"Output tokens: {usage_stats['total_output_tokens']:,}")
        print(f"Total tokens: {usage_stats['total_tokens']:,}")
        print(f"Total cost: ${usage_stats['total_cost']:.4f}")
        print("=" * 70)

        # Save summary report
        report = {
            'processing_stats': self.stats,
            'usage_stats': usage_stats,
            'model': model,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        report_path = self.data_dir / 'ai_summary_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Summary report saved to: {report_path}")

        return report


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate summaries for all chunks")
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-4o"],
        help="OpenAI model to use (default: gpt-4o-mini for cost-effectiveness)"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data_clean",
        help="Directory containing cleaned JSON files"
    )

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables!")
        print("Please add it to your .env file")
        return

    # Run summarization
    summarizer = ChunkSummarizer(data_dir=args.data_dir)
    summarizer.run(api_key=api_key, model=args.model)

    print("\n✅ Summary generation complete!")


if __name__ == "__main__":
    main()
