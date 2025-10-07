#!/usr/bin/env python3
"""
Data Quality Validation for Cleaned CompTIA Security+ Data
Validates structure, content, and readiness for RAG implementation
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class DataValidator:
    """Validate cleaned data quality and completeness"""

    def __init__(self, clean_dir: Path):
        self.clean_dir = clean_dir
        self.report = {
            'chapters': {},
            'total_documents': 0,
            'total_chunks': 0,
            'total_summaries': 0,
            'issues': [],
            'statistics': defaultdict(int)
        }

    def validate_json_structure(self, data: Dict, file_path: Path) -> List[str]:
        """Validate JSON structure and required fields"""
        issues = []

        # Check required top-level fields
        required_fields = ['metadata', 'full_content', 'chunks', 'num_chunks']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")

        # Validate metadata
        if 'metadata' in data:
            metadata = data['metadata']
            required_meta = ['chapter_num', 'section_num', 'title', 'content_type']
            for field in required_meta:
                if field not in metadata:
                    issues.append(f"Missing metadata field: {field}")

        # Validate chunks
        if 'chunks' in data:
            chunks = data['chunks']
            if not isinstance(chunks, list):
                issues.append("Chunks field is not a list")
            else:
                for idx, chunk in enumerate(chunks):
                    # Check required chunk fields
                    required_chunk_fields = ['chunk_id', 'content', 'summary', 'metadata']
                    for field in required_chunk_fields:
                        if field not in chunk:
                            issues.append(f"Chunk {idx+1}: Missing field '{field}'")

                    # Check if summary exists and is not empty
                    if 'summary' in chunk and not chunk['summary']:
                        issues.append(f"Chunk {idx+1}: Empty summary")

                    # Check if content exists
                    if 'content' in chunk and not chunk['content']:
                        issues.append(f"Chunk {idx+1}: Empty content")

        # Check document summary
        if 'document_summary' not in data:
            issues.append("Missing document-level summary")

        return issues

    def analyze_content_quality(self, data: Dict) -> Dict:
        """Analyze content quality metrics"""
        metrics = {
            'avg_chunk_length': 0,
            'avg_summary_length': 0,
            'total_words': 0,
            'chunks_count': 0,
            'has_section_headers': False,
            'has_timestamps': False
        }

        chunks = data.get('chunks', [])
        if not chunks:
            return metrics

        total_content_words = 0
        total_summary_words = 0

        for chunk in chunks:
            content = chunk.get('content', '')
            summary = chunk.get('summary', '')

            total_content_words += len(content.split())
            total_summary_words += len(summary.split())

            if chunk.get('section_header'):
                metrics['has_section_headers'] = True
            if chunk.get('timestamp_range'):
                metrics['has_timestamps'] = True

        metrics['chunks_count'] = len(chunks)
        metrics['avg_chunk_length'] = total_content_words / len(chunks) if chunks else 0
        metrics['avg_summary_length'] = total_summary_words / len(chunks) if chunks else 0
        metrics['total_words'] = total_content_words

        return metrics

    def validate_file(self, file_path: Path) -> Tuple[bool, List[str], Dict]:
        """Validate a single JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Structural validation
            issues = self.validate_json_structure(data, file_path)

            # Content quality analysis
            metrics = self.analyze_content_quality(data)

            is_valid = len(issues) == 0

            return is_valid, issues, metrics

        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"], {}
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"], {}

    def validate_chapter(self, chapter_name: str):
        """Validate all files in a chapter"""
        chapter_path = self.clean_dir / chapter_name

        if not chapter_path.exists():
            self.report['issues'].append(f"Chapter directory not found: {chapter_name}")
            return

        print(f"\nValidating {chapter_name}...")

        chapter_stats = {
            'total_files': 0,
            'valid_files': 0,
            'total_chunks': 0,
            'total_words': 0,
            'video_files': 0,
            'text_files': 0,
            'issues': []
        }

        # Validate video files
        video_dir = chapter_path / 'video'
        if video_dir.exists():
            for json_file in video_dir.glob('*.json'):
                is_valid, issues, metrics = self.validate_file(json_file)
                chapter_stats['total_files'] += 1
                chapter_stats['video_files'] += 1

                if is_valid:
                    chapter_stats['valid_files'] += 1
                    chapter_stats['total_chunks'] += metrics.get('chunks_count', 0)
                    chapter_stats['total_words'] += metrics.get('total_words', 0)
                    self.report['total_chunks'] += metrics.get('chunks_count', 0)
                else:
                    chapter_stats['issues'].extend([f"{json_file.name}: {issue}" for issue in issues])

        # Validate text files
        text_dir = chapter_path / 'text'
        if text_dir.exists():
            for json_file in text_dir.glob('*.json'):
                is_valid, issues, metrics = self.validate_file(json_file)
                chapter_stats['total_files'] += 1
                chapter_stats['text_files'] += 1

                if is_valid:
                    chapter_stats['valid_files'] += 1
                    chapter_stats['total_chunks'] += metrics.get('chunks_count', 0)
                    chapter_stats['total_words'] += metrics.get('total_words', 0)
                    self.report['total_chunks'] += metrics.get('chunks_count', 0)
                else:
                    chapter_stats['issues'].extend([f"{json_file.name}: {issue}" for issue in issues])

        self.report['chapters'][chapter_name] = chapter_stats
        self.report['total_documents'] += chapter_stats['valid_files']

        # Print chapter summary
        print(f"  Files: {chapter_stats['valid_files']}/{chapter_stats['total_files']} valid")
        print(f"  Video: {chapter_stats['video_files']}, Text: {chapter_stats['text_files']}")
        print(f"  Chunks: {chapter_stats['total_chunks']}")
        print(f"  Total words: {chapter_stats['total_words']:,}")

        if chapter_stats['issues']:
            print(f"  ⚠ Issues found: {len(chapter_stats['issues'])}")

    def generate_summary_report(self):
        """Generate and print summary report"""
        print("\n" + "=" * 60)
        print("Data Quality Validation Report")
        print("=" * 60)

        print(f"\n📊 Overall Statistics:")
        print(f"  Total documents: {self.report['total_documents']}")
        print(f"  Total chunks: {self.report['total_chunks']}")

        print(f"\n📁 By Chapter:")
        for chapter_name, stats in self.report['chapters'].items():
            print(f"\n  {chapter_name}:")
            print(f"    Documents: {stats['valid_files']}")
            print(f"    Chunks: {stats['total_chunks']}")
            print(f"    Words: {stats['total_words']:,}")
            print(f"    Video files: {stats['video_files']}")
            print(f"    Text files: {stats['text_files']}")

        # Issues summary
        total_issues = sum(len(stats['issues']) for stats in self.report['chapters'].values())
        if total_issues > 0:
            print(f"\n⚠ Total Issues: {total_issues}")
            print("\nSample Issues (first 10):")
            all_issues = []
            for stats in self.report['chapters'].values():
                all_issues.extend(stats['issues'])
            for issue in all_issues[:10]:
                print(f"  - {issue}")
        else:
            print("\n✓ No validation issues found!")

        # Calculate quality metrics
        avg_chunks_per_doc = self.report['total_chunks'] / self.report['total_documents'] if self.report['total_documents'] > 0 else 0
        print(f"\n📈 Quality Metrics:")
        print(f"  Average chunks per document: {avg_chunks_per_doc:.1f}")

        # RAG Readiness
        print(f"\n🚀 RAG Readiness:")
        is_ready = total_issues == 0 and self.report['total_chunks'] > 0
        if is_ready:
            print("  ✓ Data is ready for RAG implementation")
            print("  ✓ All documents have proper structure")
            print("  ✓ All chunks have summaries for embeddings")
            print("  ✓ Metadata is complete for filtering")
        else:
            print("  ⚠ Data needs attention before RAG implementation")

        return is_ready

    def save_report(self, output_path: Path):
        """Save validation report to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 Full report saved to: {output_path}")

    def run(self, chapters: List[str] = None):
        """Run validation on all chapters"""
        if chapters is None:
            chapters = [
                '01_Security_Concepts',
                '02_Threats_Vulnerabilities_and_Mitigations',
                '03_Cryptographic_Solutions',
                '04_Identity_and_Access_Management'
            ]

        print("=" * 60)
        print("Data Quality Validation")
        print("=" * 60)

        for chapter_name in chapters:
            self.validate_chapter(chapter_name)

        # Generate and display summary
        is_ready = self.generate_summary_report()

        # Save detailed report
        report_path = self.clean_dir / 'validation_report.json'
        self.save_report(report_path)

        return is_ready


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    clean_dir = script_dir / 'data_clean'

    if not clean_dir.exists():
        print(f"Error: Clean data directory not found: {clean_dir}")
        print("Please run data_cleaner.py first")
        return

    validator = DataValidator(clean_dir)
    is_ready = validator.run()

    if is_ready:
        print("\n✅ Data validation complete - Ready for RAG!")
    else:
        print("\n⚠️  Data validation complete - Issues need attention")


if __name__ == '__main__':
    main()
