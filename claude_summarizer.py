#!/usr/bin/env python3
"""
AI-Powered Summary Generation using Claude 3.5 Sonnet
Replaces extractive summaries with Claude-generated summaries optimized for RAG embeddings
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from anthropic import Anthropic
from tqdm import tqdm


@dataclass
class ProcessingStats:
    """Track processing statistics"""
    chunks_processed: int = 0
    documents_processed: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def add_usage(self, input_tokens: int, output_tokens: int):
        """Add token usage and calculate cost"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Claude 3.5 Sonnet pricing (as of 2024)
        input_cost = (input_tokens / 1000) * 0.003  # $3 per million
        output_cost = (output_tokens / 1000) * 0.015  # $15 per million

        self.total_cost += (input_cost + output_cost)


class ClaudeSummarizer:
    """Generate AI-powered summaries using Claude 3.5 Sonnet"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude summarizer

        Args:
            api_key: Anthropic API key
            model: Claude model to use (default: Claude 3.5 Sonnet)
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.stats = ProcessingStats()

        # Knowledge base context for CompTIA Security+
        self.kb_context = (
            "This is CompTIA Security+ certification training material covering "
            "security fundamentals, threat management, cryptography, identity and "
            "access management, network security, and compliance."
        )

    def build_summary_prompt(self, chunk: Dict, metadata: Dict) -> str:
        """
        Build context-aware prompt for Claude

        Args:
            chunk: Chunk data with content and section info
            metadata: Document metadata

        Returns:
            Formatted prompt string
        """
        content = chunk.get('content', '')
        section_header = chunk.get('section_header', '')

        chapter_title = metadata.get('title', '')
        chapter_num = metadata.get('chapter_num', '')
        content_type = metadata.get('content_type', '')

        prompt = f"""You are tasked with creating a concise summary of CompTIA Security+ training content.

Knowledge base context:
{self.kb_context}

Document context:
- Chapter {chapter_num}: {chapter_title}
- Content type: {content_type}
- Section: {section_header}

Content to summarize:
{content}

Create a 2-3 sentence summary that:
1. Captures the key security concepts and definitions
2. Is optimized for semantic search and retrieval
3. Is precise and direct - every word counts
4. Focuses on actionable security information

Provide ONLY the summary. No preamble or explanations."""

        return prompt

    def generate_summary(self, chunk: Dict, metadata: Dict) -> Optional[str]:
        """
        Generate summary for a single chunk using Claude

        Args:
            chunk: Chunk data
            metadata: Document metadata

        Returns:
            Generated summary or None if error
        """
        try:
            prompt = self.build_summary_prompt(chunk, metadata)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract summary
            summary = response.content[0].text.strip()

            # Track usage
            self.stats.add_usage(
                response.usage.input_tokens,
                response.usage.output_tokens
            )
            self.stats.chunks_processed += 1

            return summary

        except Exception as e:
            error_msg = f"Error generating summary for chunk {chunk.get('chunk_id')}: {str(e)}"
            self.stats.errors.append(error_msg)
            return None

    def process_document(self, json_path: Path, dry_run: bool = False) -> bool:
        """
        Process a single JSON document and update summaries

        Args:
            json_path: Path to JSON file
            dry_run: If True, don't save changes

        Returns:
            True if successful
        """
        try:
            # Load document
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            metadata = data.get('metadata', {})
            chunks = data.get('chunks', [])

            if not chunks:
                return True

            # Process each chunk
            for chunk in chunks:
                # Generate new summary
                new_summary = self.generate_summary(chunk, metadata)

                if new_summary:
                    chunk['summary'] = new_summary
                else:
                    # Keep existing summary on error
                    pass

                # Rate limiting - respect Anthropic's limits
                time.sleep(0.02)  # ~50 requests/second max

            # Save updated document (unless dry run)
            if not dry_run:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

            self.stats.documents_processed += 1
            return True

        except Exception as e:
            error_msg = f"Error processing {json_path.name}: {str(e)}"
            self.stats.errors.append(error_msg)
            return False

    def collect_json_files(self, clean_dir: Path, chapters: List[str]) -> List[Path]:
        """
        Collect all JSON files to process

        Args:
            clean_dir: Root data_clean directory
            chapters: List of chapter folder names

        Returns:
            List of JSON file paths
        """
        json_files = []

        for chapter_name in chapters:
            chapter_path = clean_dir / chapter_name
            if not chapter_path.exists():
                continue

            # Collect from video/ and text/ subdirectories
            for subdir in ['video', 'text']:
                subdir_path = chapter_path / subdir
                if subdir_path.exists():
                    json_files.extend(subdir_path.glob('*.json'))

        # Filter out chapter_overview.json files
        json_files = [f for f in json_files if 'overview' not in f.name.lower()]

        return sorted(json_files)

    def run(self, clean_dir: Path, chapters: List[str] = None,
            dry_run: bool = False, max_chunks: int = None):
        """
        Run summarization pipeline

        Args:
            clean_dir: Path to data_clean directory
            chapters: List of chapters to process (None = all)
            dry_run: If True, process but don't save
            max_chunks: Maximum chunks to process (for testing)
        """
        if chapters is None:
            chapters = [
                '01_Security_Concepts',
                '02_Threats_Vulnerabilities_and_Mitigations',
                '03_Cryptographic_Solutions',
                '04_Identity_and_Access_Management'
            ]

        # Collect files
        json_files = self.collect_json_files(clean_dir, chapters)

        if not json_files:
            print("No JSON files found to process")
            return

        mode = "DRY RUN" if dry_run else "PRODUCTION"
        print("=" * 60)
        print(f"Claude AI Summary Generation - {mode}")
        print("=" * 60)
        print(f"Model: {self.model}")
        print(f"Documents to process: {len(json_files)}")
        if max_chunks:
            print(f"Max chunks: {max_chunks}")
        if dry_run:
            print("⚠️  DRY RUN MODE - Changes will NOT be saved")
        print()

        # Process files with progress bar
        for json_file in tqdm(json_files, desc="Processing documents"):
            # Check if we've hit max chunks limit
            if max_chunks and self.stats.chunks_processed >= max_chunks:
                print(f"\n✓ Reached max chunks limit ({max_chunks})")
                break

            self.process_document(json_file, dry_run=dry_run)

        # Print results
        self.print_summary()

        # Save report
        if not dry_run:
            self.save_report(clean_dir)

    def print_summary(self):
        """Print processing summary"""
        print("\n" + "=" * 60)
        print("Processing Summary")
        print("=" * 60)
        print(f"Documents processed: {self.stats.documents_processed}")
        print(f"Chunks processed: {self.stats.chunks_processed}")
        print(f"Total input tokens: {self.stats.total_input_tokens:,}")
        print(f"Total output tokens: {self.stats.total_output_tokens:,}")
        print(f"Total cost: ${self.stats.total_cost:.4f}")

        if self.stats.errors:
            print(f"\n⚠️  Errors encountered: {len(self.stats.errors)}")
            for error in self.stats.errors[:5]:
                print(f"  - {error}")
        else:
            print("\n✓ No errors")

        print("=" * 60)

    def save_report(self, clean_dir: Path):
        """Save processing report to JSON"""
        report_path = clean_dir / 'ai_summary_report.json'

        report = {
            'model': self.model,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': asdict(self.stats),
            'cost_breakdown': {
                'input_tokens': self.stats.total_input_tokens,
                'output_tokens': self.stats.total_output_tokens,
                'input_cost': (self.stats.total_input_tokens / 1000) * 0.003,
                'output_cost': (self.stats.total_output_tokens / 1000) * 0.015,
                'total_cost': self.stats.total_cost
            }
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Report saved to: {report_path}")


def main():
    """Main entry point"""
    import argparse
    from dotenv import load_dotenv

    parser = argparse.ArgumentParser(
        description='Generate AI summaries using Claude 3.5 Sonnet'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Process chunks but do not save changes'
    )
    parser.add_argument(
        '--max-chunks',
        type=int,
        help='Maximum number of chunks to process (for testing)'
    )
    parser.add_argument(
        '--chapter',
        type=str,
        help='Process specific chapter only (e.g., 01)'
    )

    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()

    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found")
        print("Please set it in .env file or environment variable")
        print("\nOption 1 - Create .env file:")
        print("  echo 'ANTHROPIC_API_KEY=your-key-here' > .env")
        print("\nOption 2 - Set environment variable:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    # Setup paths
    script_dir = Path(__file__).parent
    clean_dir = script_dir / 'data_clean'

    if not clean_dir.exists():
        print(f"Error: {clean_dir} not found")
        return

    # Determine chapters to process
    chapters = None
    if args.chapter:
        chapters = [f"{args.chapter.zfill(2)}_*"]
        # Find matching chapter folder
        matching = list(clean_dir.glob(f"{args.chapter.zfill(2)}_*"))
        if matching:
            chapters = [matching[0].name]
        else:
            print(f"Error: Chapter {args.chapter} not found")
            return

    # Initialize summarizer
    summarizer = ClaudeSummarizer(api_key)

    # Run
    summarizer.run(
        clean_dir=clean_dir,
        chapters=chapters,
        dry_run=args.dry_run,
        max_chunks=args.max_chunks
    )


if __name__ == '__main__':
    main()
