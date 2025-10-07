#!/usr/bin/env python3
"""
OpenAI Embedding Generator for CompTIA Security+ RAG System
Alternative to Voyage AI with better rate limits
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, asdict
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class EmbeddingChunk:
    """Data class for chunk with embedding"""
    chunk_id: str
    embedding: List[float]
    content: str
    summary: str
    section_header: str
    metadata: Dict


class OpenAIEmbedder:
    """OpenAI embedding generator"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedder

        Args:
            api_key: OpenAI API key
            model: Model to use (text-embedding-3-small or text-embedding-3-large)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

        # Model dimensions
        self.model_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }

        # Usage tracking
        self.total_tokens = 0
        self.total_cost = 0.0

        # Pricing (per million tokens)
        self.pricing = {
            "text-embedding-3-small": 0.02,
            "text-embedding-3-large": 0.13
        }

    def create_combined_text(self, chunk: Dict) -> str:
        """
        Create combined text for embedding: section_header + summary + content

        Args:
            chunk: Chunk dictionary with content, summary, section_header

        Returns:
            Combined text string
        """
        section_header = chunk.get('section_header', '')
        summary = chunk.get('summary', '')
        content = chunk.get('content', '')

        # Format: Header\n\nSummary\n\nContent
        combined = f"{section_header}\n\n{summary}\n\n{content}"
        return combined.strip()

    def generate_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for texts using OpenAI

        Args:
            texts: List of text strings to embed
            batch_size: Batch size (OpenAI can handle larger batches)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        print(f"\n🌐 Calling OpenAI API...")

        # Process in batches with progress bar
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch = texts[i:i + batch_size]

            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(embeddings)

                # Track usage
                self.total_tokens += response.usage.total_tokens

                # Calculate cost
                cost = (response.usage.total_tokens / 1_000_000) * self.pricing.get(self.model, 0.02)
                self.total_cost += cost

            except Exception as e:
                print(f"\n❌ Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Return zero vectors as fallback
                dim = self.model_dims.get(self.model, 1536)
                all_embeddings.extend([[0.0] * dim for _ in batch])

        return all_embeddings

    def get_usage_stats(self) -> Dict:
        """Get usage statistics"""
        return {
            "model": self.model,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "embedding_dimension": self.model_dims.get(self.model, 1536)
        }


class EmbeddingGenerator:
    """Main embedding generation pipeline"""

    def __init__(self, data_dir: str = "data_clean", output_file: str = "embeddings.json"):
        """
        Initialize embedding generator

        Args:
            data_dir: Directory containing cleaned JSON files
            output_file: Output file for embeddings
        """
        self.data_dir = Path(data_dir)
        self.output_file = output_file
        self.chunks: List[Dict] = []

    def load_chunks(self) -> int:
        """
        Load all chunks from JSON files

        Returns:
            Number of chunks loaded
        """
        print("📂 Loading chunks from JSON files...")

        # Find all JSON files (excluding chapter_overview and validation_report)
        json_files = []
        for json_file in self.data_dir.rglob("*.json"):
            if json_file.name not in ['chapter_overview.json', 'validation_report.json', 'ai_summary_report.json']:
                json_files.append(json_file)

        # Load chunks from each file
        for json_file in tqdm(json_files, desc="Loading files"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract chunks
                chunks = data.get('chunks', [])
                self.chunks.extend(chunks)

            except Exception as e:
                print(f"\n⚠️  Error loading {json_file}: {e}")

        print(f"✅ Loaded {len(self.chunks)} chunks from {len(json_files)} files")
        return len(self.chunks)

    def generate_all_embeddings(
        self,
        embedder: OpenAIEmbedder,
        batch_size: int = 100
    ) -> List[EmbeddingChunk]:
        """
        Generate embeddings for all chunks

        Args:
            embedder: OpenAIEmbedder instance
            batch_size: Batch size for API calls

        Returns:
            List of EmbeddingChunk objects
        """
        print(f"\n🔄 Generating embeddings for {len(self.chunks)} chunks...")
        print(f"Model: {embedder.model}")
        print(f"Batch size: {batch_size}")

        # Create combined texts
        print("\n📝 Preparing combined texts...")
        combined_texts = []
        for chunk in tqdm(self.chunks, desc="Preparing texts"):
            combined = embedder.create_combined_text(chunk)
            combined_texts.append(combined)

        # Generate embeddings
        embeddings = embedder.generate_embeddings(combined_texts, batch_size=batch_size)

        # Create EmbeddingChunk objects
        embedding_chunks = []
        for chunk, embedding in zip(self.chunks, embeddings):
            embedding_chunk = EmbeddingChunk(
                chunk_id=chunk.get('chunk_id', ''),
                embedding=embedding,
                content=chunk.get('content', ''),
                summary=chunk.get('summary', ''),
                section_header=chunk.get('section_header', ''),
                metadata=chunk.get('metadata', {})
            )
            embedding_chunks.append(embedding_chunk)

        return embedding_chunks

    def save_embeddings(self, embedding_chunks: List[EmbeddingChunk]) -> None:
        """
        Save embeddings to JSON file

        Args:
            embedding_chunks: List of EmbeddingChunk objects
        """
        print(f"\n💾 Saving embeddings to {self.output_file}...")

        # Convert to dictionaries
        data = {
            "num_chunks": len(embedding_chunks),
            "embedding_dimension": len(embedding_chunks[0].embedding) if embedding_chunks else 0,
            "chunks": [asdict(chunk) for chunk in embedding_chunks]
        }

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        # Get file size
        file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
        print(f"✅ Saved {len(embedding_chunks)} embeddings ({file_size:.2f} MB)")

    def generate(self, api_key: str, model: str = "text-embedding-3-small", batch_size: int = 100) -> None:
        """
        Main pipeline: load chunks, generate embeddings, save

        Args:
            api_key: OpenAI API key
            model: Model to use
            batch_size: Batch size for API calls
        """
        print("=" * 60)
        print("EMBEDDING GENERATION - OPENAI")
        print("=" * 60)

        # Load chunks
        num_chunks = self.load_chunks()
        if num_chunks == 0:
            print("❌ No chunks found!")
            return

        # Initialize embedder
        embedder = OpenAIEmbedder(api_key=api_key, model=model)

        # Generate embeddings
        embedding_chunks = self.generate_all_embeddings(embedder, batch_size=batch_size)

        # Save embeddings
        self.save_embeddings(embedding_chunks)

        # Print usage stats
        stats = embedder.get_usage_stats()
        print("\n" + "=" * 60)
        print("USAGE STATISTICS")
        print("=" * 60)
        print(f"Model: {stats['model']}")
        print(f"Embedding dimension: {stats['embedding_dimension']}")
        print(f"Total tokens: {stats['total_tokens']:,}")
        print(f"Total cost: ${stats['total_cost']:.4f}")
        print("=" * 60)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings using OpenAI")
    parser.add_argument(
        "--model",
        type=str,
        default="text-embedding-3-small",
        choices=["text-embedding-3-small", "text-embedding-3-large"],
        help="OpenAI model to use"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for API calls"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data_clean",
        help="Directory containing cleaned JSON files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="embeddings.json",
        help="Output file for embeddings"
    )

    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables!")
        print("Please add it to your .env file")
        return

    # Run generation
    generator = EmbeddingGenerator(data_dir=args.data_dir, output_file=args.output)
    generator.generate(api_key=api_key, model=args.model, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
