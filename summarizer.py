#!/usr/bin/env python3
"""
Generate summaries for cleaned data chunks using extractive summarization
Optimized for RAG embeddings and semantic search
"""

import json
import os
from pathlib import Path
from typing import Dict, List
import re


class SimpleSummarizer:
    """
    Extractive summarization for content chunks
    Creates concise summaries suitable for embedding and retrieval
    """

    def __init__(self):
        self.stats = {
            'total_chunks': 0,
            'summarized_chunks': 0,
            'total_documents': 0
        }

    def extract_key_sentences(self, text: str, max_sentences: int = 2) -> str:
        """
        Extract key sentences from text using simple heuristics
        Prioritizes sentences with important keywords and proper structure
        """
        if not text or len(text.split()) < 10:
            return text

        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]

        if not sentences:
            return text[:200] + "..." if len(text) > 200 else text

        # Score sentences based on important keywords
        security_keywords = [
            'security', 'attack', 'threat', 'vulnerability', 'encryption',
            'authentication', 'authorization', 'malware', 'firewall', 'network',
            'data', 'access', 'control', 'risk', 'compliance', 'protection',
            'breach', 'incident', 'defense', 'cyber', 'policy', 'management'
        ]

        scored_sentences = []
        for sentence in sentences:
            score = 0
            lower_sent = sentence.lower()

            # Count keyword occurrences
            for keyword in security_keywords:
                if keyword in lower_sent:
                    score += 2

            # Prefer sentences with definitions or key concepts
            if any(phrase in lower_sent for phrase in ['is defined as', 'refers to', 'means that', 'is the process']):
                score += 3

            # Prefer shorter, more focused sentences
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                score += 2
            elif word_count > 50:
                score -= 1

            # Prefer sentences at the beginning
            if sentences.index(sentence) < 2:
                score += 1

            scored_sentences.append((score, sentence))

        # Sort by score and select top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        top_sentences = [s[1] for s in scored_sentences[:max_sentences]]

        # Return in original order
        result_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                result_sentences.append(sentence)
                if len(result_sentences) >= max_sentences:
                    break

        summary = '. '.join(result_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'

        return summary

    def generate_chunk_summary(self, chunk: Dict) -> str:
        """Generate summary for a single chunk"""
        content = chunk.get('content', '')
        section_header = chunk.get('section_header', '')
        metadata = chunk.get('metadata', {})

        # For very short content, use as-is
        if len(content.split()) < 30:
            return content

        # Create summary
        summary_parts = []

        # Include section header context if available
        if section_header and section_header not in ['Introduction', 'Summary']:
            summary_parts.append(f"{section_header}:")

        # Extract key sentences
        key_content = self.extract_key_sentences(content, max_sentences=2)
        summary_parts.append(key_content)

        summary = ' '.join(summary_parts)

        # Add metadata context for better retrieval
        title = metadata.get('title', '')
        if title and len(summary) < 150:
            summary = f"[{title}] {summary}"

        return summary

    def generate_document_summary(self, chunks: List[Dict], metadata: Dict) -> str:
        """Generate overall summary for entire document"""
        title = metadata.get('title', '')
        content_type = metadata.get('content_type', '')

        # Collect content from all chunks
        all_content = ' '.join([chunk.get('content', '') for chunk in chunks])

        # Generate document-level summary
        doc_summary = self.extract_key_sentences(all_content, max_sentences=3)

        # Create structured summary
        summary = f"{title} ({content_type}): {doc_summary}"

        return summary

    def process_json_file(self, file_path: Path) -> bool:
        """Process a single JSON file and add summaries"""
        try:
            # Read existing data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.stats['total_documents'] += 1

            # Generate chunk summaries
            chunks = data.get('chunks', [])
            for chunk in chunks:
                if not chunk.get('summary'):  # Only if summary doesn't exist
                    chunk['summary'] = self.generate_chunk_summary(chunk)
                    self.stats['summarized_chunks'] += 1
                self.stats['total_chunks'] += 1

            # Generate document summary
            if 'document_summary' not in data:
                data['document_summary'] = self.generate_document_summary(
                    chunks, data.get('metadata', {})
                )

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error processing {file_path.name}: {str(e)}")
            return False

    def process_chapter(self, chapter_dir: Path):
        """Process all JSON files in a chapter directory"""
        if not chapter_dir.exists():
            print(f"Chapter directory not found: {chapter_dir}")
            return

        print(f"\nProcessing {chapter_dir.name}...")

        file_count = 0

        # Process video files
        video_dir = chapter_dir / 'video'
        if video_dir.exists():
            for json_file in video_dir.glob('*.json'):
                if self.process_json_file(json_file):
                    file_count += 1

        # Process text files
        text_dir = chapter_dir / 'text'
        if text_dir.exists():
            for json_file in text_dir.glob('*.json'):
                if self.process_json_file(json_file):
                    file_count += 1

        print(f"  Summarized {file_count} documents")

    def run(self, clean_dir: Path, chapters: List[str] = None):
        """Run summarization on all chapters"""
        if chapters is None:
            chapters = [
                '01_Security_Concepts',
                '02_Threats_Vulnerabilities_and_Mitigations',
                '03_Cryptographic_Solutions',
                '04_Identity_and_Access_Management'
            ]

        print("=" * 60)
        print("Content Summarization for RAG Embeddings")
        print("=" * 60)

        for chapter_name in chapters:
            chapter_path = clean_dir / chapter_name
            self.process_chapter(chapter_path)

        print("\n" + "=" * 60)
        print("Summarization Statistics:")
        print("=" * 60)
        print(f"Total documents processed: {self.stats['total_documents']}")
        print(f"Total chunks: {self.stats['total_chunks']}")
        print(f"Summaries generated: {self.stats['summarized_chunks']}")


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    clean_dir = script_dir / 'data_clean'

    if not clean_dir.exists():
        print(f"Error: Clean data directory not found: {clean_dir}")
        print("Please run data_cleaner.py first")
        return

    summarizer = SimpleSummarizer()
    summarizer.run(clean_dir)

    print("\n✓ Summarization complete!")
    print("  All chunks now have summaries optimized for RAG retrieval")


if __name__ == '__main__':
    main()
