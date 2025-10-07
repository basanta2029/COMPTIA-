#!/usr/bin/env python3
"""
CompTIA Security+ Data Cleaning Pipeline
Processes raw transcript data for RAG implementation with summary-indexed embeddings
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


@dataclass
class ContentMetadata:
    """Metadata extracted from filename and content"""
    chapter_num: str
    section_num: str
    title: str
    content_type: str  # video, text, exam, simulation, chapter_intro
    filename: str
    file_path: str
    word_count: int = 0
    has_content: bool = True


@dataclass
class ContentChunk:
    """Individual content chunk with metadata"""
    chunk_id: str
    content: str
    summary: str
    metadata: Dict
    section_header: Optional[str] = None
    timestamp_range: Optional[str] = None


class DataCleaner:
    """Main data cleaning pipeline"""

    def __init__(self, raw_dir: str, clean_dir: str):
        self.raw_dir = Path(raw_dir)
        self.clean_dir = Path(clean_dir)
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'empty_files': 0,
            'video_files': 0,
            'text_files': 0,
            'errors': []
        }

    def parse_filename(self, filename: str) -> Optional[ContentMetadata]:
        """
        Extract metadata from filename
        Format: X.Y.Z_Title_Name_[type].txt
        """
        # Remove .txt extension
        name = filename.replace('.txt', '')

        # Check for chapter introduction
        if name.startswith('Chapter_'):
            match = re.match(r'Chapter_(\d+)\.0_(.+)', name)
            if match:
                return ContentMetadata(
                    chapter_num=match.group(1),
                    section_num=f"{match.group(1)}.0",
                    title=match.group(2).replace('_', ' '),
                    content_type='chapter_intro',
                    filename=filename,
                    file_path=''
                )

        # Parse regular files: 1.2.3_Title_[type].txt
        pattern = r'^(\d+)\.(\d+)\.(\d+)_(.+?)_\[(\w+)\]$'
        match = re.match(pattern, name)

        if match:
            chapter = match.group(1)
            section = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
            title = match.group(4).replace('_', ' ')
            content_type = match.group(5)

            return ContentMetadata(
                chapter_num=chapter,
                section_num=section,
                title=title,
                content_type=content_type,
                filename=filename,
                file_path=''
            )

        return None

    def clean_video_transcript(self, content: str) -> Tuple[List[Dict], str]:
        """
        Clean video transcript: remove timestamps, extract sections
        Returns: (sections_list, full_cleaned_content)
        """
        sections = []
        current_section = None
        current_content = []

        lines = content.strip().split('\n')
        full_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section header with timestamp (e.g., "Section Name 00:00-01:23")
            timestamp_pattern = r'^(.+?)\s+(\d{2}:\d{2}-\d{2}:\d{2})$'
            match = re.match(timestamp_pattern, line)

            if match:
                # Save previous section
                if current_section and current_content:
                    sections.append({
                        'header': current_section['header'],
                        'timestamp': current_section['timestamp'],
                        'content': ' '.join(current_content)
                    })

                # Start new section
                current_section = {
                    'header': match.group(1).strip(),
                    'timestamp': match.group(2)
                }
                current_content = []
            else:
                # Regular content line - remove leading arrows/numbers
                clean_line = re.sub(r'^\d+→', '', line).strip()
                if clean_line and not re.match(r'^Click one of the buttons', clean_line):
                    current_content.append(clean_line)
                    full_text.append(clean_line)

        # Save last section
        if current_section and current_content:
            sections.append({
                'header': current_section['header'],
                'timestamp': current_section['timestamp'],
                'content': ' '.join(current_content)
            })

        return sections, ' '.join(full_text)

    def clean_text_document(self, content: str) -> Tuple[List[Dict], str]:
        """
        Clean text document: preserve structure, extract sections
        Returns: (sections_list, full_cleaned_content)
        """
        sections = []
        lines = content.strip().split('\n')
        full_text = []
        current_section = None
        current_content = []

        for line in lines:
            # Remove line numbers (e.g., "     1→")
            clean_line = re.sub(r'^\s*\d+→', '', line).strip()

            if not clean_line:
                continue

            # Check if it's a header (all caps, short, or ends with specific patterns)
            is_header = (
                clean_line.isupper() and len(clean_line.split()) <= 5 or
                re.match(r'^[\d.]+\s+[A-Z]', clean_line) or
                clean_line.endswith(':') and len(clean_line) < 80
            )

            if is_header and current_content:
                # Save previous section
                if current_section:
                    sections.append({
                        'header': current_section,
                        'content': ' '.join(current_content)
                    })
                current_section = clean_line
                current_content = []
            else:
                if current_section is None:
                    current_section = "Introduction"
                current_content.append(clean_line)
                full_text.append(clean_line)

        # Save last section
        if current_section and current_content:
            sections.append({
                'header': current_section,
                'content': ' '.join(current_content)
            })

        return sections, ' '.join(full_text)

    def process_file(self, file_path: Path, chapter_dir: str) -> Optional[Dict]:
        """Process a single file and return cleaned data"""
        self.stats['total_files'] += 1

        # Parse filename
        metadata = self.parse_filename(file_path.name)
        if not metadata:
            self.stats['errors'].append(f"Could not parse filename: {file_path.name}")
            return None

        metadata.file_path = str(file_path)

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stats['errors'].append(f"Error reading {file_path.name}: {str(e)}")
            return None

        # Skip empty files
        if not content.strip():
            self.stats['empty_files'] += 1
            metadata.has_content = False
            return None

        metadata.word_count = len(content.split())

        # Process based on content type
        sections = []
        full_content = content

        if metadata.content_type == 'video':
            self.stats['video_files'] += 1
            sections, full_content = self.clean_video_transcript(content)
        elif metadata.content_type == 'text':
            self.stats['text_files'] += 1
            sections, full_content = self.clean_text_document(content)
        elif metadata.content_type == 'chapter_intro':
            sections, full_content = self.clean_text_document(content)
        else:
            # exam, simulation files (usually empty)
            return None

        # Create chunks from sections
        chunks = []
        for idx, section in enumerate(sections):
            chunk_id = f"{metadata.section_num}_chunk_{idx+1}"

            chunk = ContentChunk(
                chunk_id=chunk_id,
                content=section['content'],
                summary="",  # Will be filled by summarization step
                metadata=asdict(metadata),
                section_header=section.get('header'),
                timestamp_range=section.get('timestamp')
            )
            chunks.append(asdict(chunk))

        result = {
            'metadata': asdict(metadata),
            'full_content': full_content,
            'chunks': chunks,
            'num_chunks': len(chunks)
        }

        self.stats['processed_files'] += 1
        return result

    def process_chapter(self, chapter_name: str, chapters_to_process: List[str]):
        """Process all files in a chapter"""
        if chapter_name not in chapters_to_process:
            return

        chapter_path = self.raw_dir / chapter_name
        if not chapter_path.exists():
            print(f"Chapter directory not found: {chapter_path}")
            return

        print(f"\nProcessing {chapter_name}...")

        # Create output directories
        output_dir = self.clean_dir / chapter_name
        video_dir = output_dir / 'video'
        text_dir = output_dir / 'text'
        video_dir.mkdir(parents=True, exist_ok=True)
        text_dir.mkdir(parents=True, exist_ok=True)

        chapter_data = []

        # Process all .txt files in chapter
        for file_path in sorted(chapter_path.glob('*.txt')):
            result = self.process_file(file_path, chapter_name)
            if result:
                chapter_data.append(result)

                # Save individual file
                metadata = result['metadata']
                if metadata['content_type'] == 'video':
                    output_path = video_dir / f"{metadata['section_num']}_{metadata['title'].replace(' ', '_')}.json"
                elif metadata['content_type'] in ['text', 'chapter_intro']:
                    output_path = text_dir / f"{metadata['section_num']}_{metadata['title'].replace(' ', '_')}.json"
                else:
                    continue

                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)

        # Save chapter overview
        overview_path = output_dir / 'chapter_overview.json'
        with open(overview_path, 'w', encoding='utf-8') as f:
            json.dump({
                'chapter': chapter_name,
                'total_documents': len(chapter_data),
                'documents': [d['metadata'] for d in chapter_data]
            }, f, indent=2, ensure_ascii=False)

        print(f"  Processed {len(chapter_data)} files")

    def run(self, chapters: List[str] = None):
        """Run the full cleaning pipeline"""
        if chapters is None:
            chapters = [
                '01_Security_Concepts',
                '02_Threats_Vulnerabilities_and_Mitigations',
                '03_Cryptographic_Solutions',
                '04_Identity_and_Access_Management'
            ]

        print("=" * 60)
        print("CompTIA Security+ Data Cleaning Pipeline")
        print("=" * 60)

        for chapter in chapters:
            self.process_chapter(chapter, chapters)

        print("\n" + "=" * 60)
        print("Cleaning Statistics:")
        print("=" * 60)
        print(f"Total files scanned: {self.stats['total_files']}")
        print(f"Successfully processed: {self.stats['processed_files']}")
        print(f"Empty files skipped: {self.stats['empty_files']}")
        print(f"Video transcripts: {self.stats['video_files']}")
        print(f"Text documents: {self.stats['text_files']}")

        if self.stats['errors']:
            print(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:10]:
                print(f"  - {error}")


def main():
    """Main entry point"""
    script_dir = Path(__file__).parent
    raw_dir = script_dir / 'data_raw'
    clean_dir = script_dir / 'data_clean'

    cleaner = DataCleaner(raw_dir, clean_dir)
    cleaner.run()

    print("\n✓ Data cleaning complete!")
    print(f"  Output directory: {clean_dir}")


if __name__ == '__main__':
    main()
