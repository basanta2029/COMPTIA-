#!/usr/bin/env python3
"""
Upload Embeddings to Qdrant Cloud
One-time script to migrate local embeddings to Qdrant Cloud cluster
"""

import os
from dotenv import load_dotenv
from vector_db_manager import VectorDBManager

# Load environment variables
load_dotenv()


def main():
    """Upload embeddings to Qdrant Cloud"""
    print("=" * 60)
    print("QDRANT CLOUD UPLOAD")
    print("=" * 60)

    # Get Qdrant Cloud credentials
    qdrant_url = os.getenv("QDRANT_CLOUD_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")

    if not qdrant_url or not qdrant_api_key:
        print("❌ Error: QDRANT_CLOUD_URL and QDRANT_API_KEY must be set in .env")
        print("\nPlease add:")
        print("  QDRANT_CLOUD_URL=https://your-cluster.cloud.qdrant.io")
        print("  QDRANT_API_KEY=your-api-key-here")
        return

    print(f"\n☁️  Cloud URL: {qdrant_url}")
    print(f"🔑 API Key: {qdrant_api_key[:20]}...")

    # Confirm upload
    print("\n⚠️  This will upload 2,321 embeddings (108MB) to Qdrant Cloud.")
    print("   This takes approximately 2-3 minutes.")
    confirm = input("\nProceed with upload? (yes/no): ")

    if confirm.lower() != "yes":
        print("❌ Upload cancelled")
        return

    print("\n" + "=" * 60)

    # Initialize VectorDBManager with cloud credentials
    manager = VectorDBManager(
        collection_name="comptia_security_plus",
        embedding_dim=1536,
        url=qdrant_url,
        api_key=qdrant_api_key
    )

    # Create collection
    print("\n📦 Creating collection...")
    manager.create_collection(recreate=False)

    # Upload embeddings
    print("\n📤 Uploading embeddings from embeddings.json...")
    print("   (This may take 2-3 minutes...)")

    try:
        count = manager.upload_embeddings(
            embeddings_file="embeddings.json",
            batch_size=100
        )

        print("\n" + "=" * 60)
        print("✅ UPLOAD SUCCESSFUL!")
        print("=" * 60)
        print(f"Uploaded {count} chunks to Qdrant Cloud")

        # Verify collection
        print("\n🔍 Verifying collection...")
        info = manager.get_collection_info()

        print(f"\nCollection Info:")
        print(f"  Name: {info.get('collection_name')}")
        print(f"  Vectors: {info.get('vectors_count'):,}")
        print(f"  Dimension: {info.get('vector_size')}")
        print(f"  Distance: {info.get('distance')}")
        print(f"  Status: {info.get('status')}")

        if info.get('vectors_count') == count:
            print("\n✅ Verification passed! All vectors uploaded successfully.")
        else:
            print(f"\n⚠️  Warning: Expected {count} vectors, found {info.get('vectors_count')}")

        print("\n" + "=" * 60)
        print("🎉 You can now deploy to Streamlit Cloud!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Test locally with: python -c 'from rag_pipeline import RAGPipeline; p = RAGPipeline(); print(p.query(\"What is phishing?\", k=3).answer)'")
        print("2. Update .gitignore to exclude embeddings.json")
        print("3. Commit and push to GitHub")
        print("4. Deploy to Streamlit Community Cloud")

    except Exception as e:
        print(f"\n❌ Upload failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify your Qdrant Cloud credentials in .env")
        print("3. Ensure you have enough storage in your Qdrant Cloud free tier (1GB)")
        return


if __name__ == "__main__":
    main()
