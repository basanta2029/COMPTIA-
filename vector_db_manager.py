#!/usr/bin/env python3
"""
Vector Database Manager for CompTIA Security+ RAG System
Manages Qdrant vector database for summary-indexed retrieval
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)
from tqdm import tqdm


@dataclass
class SearchResult:
    """Search result with content and metadata"""
    chunk_id: str
    content: str
    summary: str
    section_header: str
    score: float
    metadata: Dict


class VectorDBManager:
    """Qdrant vector database manager"""

    def __init__(
        self,
        collection_name: str = "comptia_security_plus",
        host: str = "localhost",
        port: int = 6333,
        embedding_dim: int = 1536,
        use_memory: bool = False
    ):
        """
        Initialize vector database manager

        Args:
            collection_name: Name of the Qdrant collection
            host: Qdrant server host
            port: Qdrant server port
            embedding_dim: Dimension of embedding vectors
            use_memory: If True, use in-memory mode (no Docker required)
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # Connect to Qdrant
        if use_memory:
            print(f"🧠 Using Qdrant in-memory mode (no Docker required)...")
            self.client = QdrantClient(":memory:")
        else:
            try:
                print(f"🔌 Connecting to Qdrant at {host}:{port}...")
                self.client = QdrantClient(host=host, port=port, timeout=5)
                # Test connection
                self.client.get_collections()
                print(f"✅ Connected to Qdrant server")
            except Exception as e:
                print(f"⚠️  Cannot connect to Qdrant server: {e}")
                print(f"🧠 Falling back to in-memory mode...")
                self.client = QdrantClient(":memory:")

    def create_collection(self, recreate: bool = False) -> None:
        """
        Create Qdrant collection with appropriate schema

        Args:
            recreate: If True, delete and recreate collection
        """
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_exists = any(c.name == self.collection_name for c in collections)

        if collection_exists:
            if recreate:
                print(f"🗑️  Deleting existing collection '{self.collection_name}'...")
                self.client.delete_collection(collection_name=self.collection_name)
            else:
                print(f"✅ Collection '{self.collection_name}' already exists")
                return

        # Create new collection
        print(f"🆕 Creating collection '{self.collection_name}'...")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.embedding_dim,
                distance=Distance.COSINE
            )
        )

        # Create payload indexes for filtering
        print("📇 Creating payload indexes...")

        # Index for chapter_num
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.chapter_num",
            field_schema="keyword"
        )

        # Index for section_num
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.section_num",
            field_schema="keyword"
        )

        # Index for content_type
        self.client.create_payload_index(
            collection_name=self.collection_name,
            field_name="metadata.content_type",
            field_schema="keyword"
        )

        print(f"✅ Collection '{self.collection_name}' created successfully")

    def upload_embeddings(
        self,
        embeddings_file: str = "embeddings.json",
        batch_size: int = 100
    ) -> int:
        """
        Upload embeddings to Qdrant

        Args:
            embeddings_file: Path to embeddings JSON file
            batch_size: Batch size for uploads

        Returns:
            Number of chunks uploaded
        """
        print(f"\n📤 Uploading embeddings from {embeddings_file}...")

        # Load embeddings
        with open(embeddings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = data['chunks']
        total_chunks = len(chunks)

        print(f"Total chunks to upload: {total_chunks}")
        print(f"Embedding dimension: {data.get('embedding_dimension', self.embedding_dim)}")

        # Upload in batches
        uploaded = 0
        for i in tqdm(range(0, total_chunks, batch_size), desc="Uploading batches"):
            batch = chunks[i:i + batch_size]

            # Create points
            points = []
            for idx, chunk in enumerate(batch):
                point_id = uploaded + idx

                # Create payload
                payload = {
                    "chunk_id": chunk['chunk_id'],
                    "content": chunk['content'],
                    "summary": chunk['summary'],
                    "section_header": chunk['section_header'],
                    "metadata": chunk['metadata']
                }

                # Create point
                point = PointStruct(
                    id=point_id,
                    vector=chunk['embedding'],
                    payload=payload
                )
                points.append(point)

            # Upload batch
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            uploaded += len(batch)

        print(f"✅ Uploaded {uploaded} chunks to collection '{self.collection_name}'")
        return uploaded

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        chapter_filter: Optional[str] = None,
        content_type_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Semantic search in vector database

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            chapter_filter: Filter by chapter number (e.g., "1")
            content_type_filter: Filter by content type (e.g., "video", "text")

        Returns:
            List of SearchResult objects
        """
        # Build filter
        search_filter = None
        if chapter_filter or content_type_filter:
            conditions = []

            if chapter_filter:
                conditions.append(
                    FieldCondition(
                        key="metadata.chapter_num",
                        match=MatchValue(value=chapter_filter)
                    )
                )

            if content_type_filter:
                conditions.append(
                    FieldCondition(
                        key="metadata.content_type",
                        match=MatchValue(value=content_type_filter)
                    )
                )

            search_filter = Filter(must=conditions)

        # Perform search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            query_filter=search_filter
        )

        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_result = SearchResult(
                chunk_id=result.payload['chunk_id'],
                content=result.payload['content'],
                summary=result.payload['summary'],
                section_header=result.payload['section_header'],
                score=result.score,
                metadata=result.payload['metadata']
            )
            search_results.append(search_result)

        return search_results

    def get_collection_info(self) -> Dict:
        """
        Get collection information

        Returns:
            Dictionary with collection stats
        """
        try:
            info = self.client.get_collection(collection_name=self.collection_name)

            return {
                "collection_name": self.collection_name,
                "vectors_count": info.points_count,
                "segments_count": info.segments_count,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance,
                "status": info.status
            }
        except Exception as e:
            return {"error": str(e)}

    def delete_collection(self) -> None:
        """Delete the collection"""
        print(f"🗑️  Deleting collection '{self.collection_name}'...")
        self.client.delete_collection(collection_name=self.collection_name)
        print("✅ Collection deleted")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Manage Qdrant vector database")
    parser.add_argument(
        "--action",
        type=str,
        choices=["create", "upload", "info", "delete"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--embeddings",
        type=str,
        default="embeddings.json",
        help="Path to embeddings JSON file"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="comptia_security_plus",
        help="Collection name"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Qdrant host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6333,
        help="Qdrant port"
    )
    parser.add_argument(
        "--embedding-dim",
        type=int,
        default=1536,
        help="Embedding dimension (1536 for text-embedding-3-small)"
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate collection if it exists"
    )

    args = parser.parse_args()

    # Initialize manager
    manager = VectorDBManager(
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        embedding_dim=args.embedding_dim
    )

    # Perform action
    if args.action == "create":
        manager.create_collection(recreate=args.recreate)

    elif args.action == "upload":
        # First ensure collection exists
        manager.create_collection(recreate=False)
        # Then upload
        manager.upload_embeddings(embeddings_file=args.embeddings)

    elif args.action == "info":
        info = manager.get_collection_info()
        print("\n" + "=" * 60)
        print("COLLECTION INFO")
        print("=" * 60)
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 60)

    elif args.action == "delete":
        confirm = input(f"⚠️  Delete collection '{args.collection}'? (yes/no): ")
        if confirm.lower() == "yes":
            manager.delete_collection()
        else:
            print("❌ Cancelled")


if __name__ == "__main__":
    main()
