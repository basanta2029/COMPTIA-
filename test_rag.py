#!/usr/bin/env python3
"""
Manual Testing Script for CompTIA Security+ RAG System
Test suite with sample security questions
"""

from rag_pipeline import RAGPipeline
from typing import List, Dict


# Sample CompTIA Security+ test questions
TEST_QUESTIONS = [
    {
        "query": "What is phishing?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "Explain two-factor authentication",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "What is the CIA triad?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "What are the different types of malware?",
        "k": 5,
        "chapter_filter": None
    },
    {
        "query": "How does encryption work?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "What is a firewall?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "Explain the difference between symmetric and asymmetric encryption",
        "k": 4,
        "chapter_filter": None
    },
    {
        "query": "What is social engineering?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "What are the principles of least privilege?",
        "k": 3,
        "chapter_filter": None
    },
    {
        "query": "How do VPNs work?",
        "k": 3,
        "chapter_filter": None
    }
]


def run_single_test(pipeline: RAGPipeline, test: Dict) -> None:
    """Run a single test query"""
    print("\n" + "=" * 80)
    print(f"TEST QUERY: {test['query']}")
    print("=" * 80)

    # Run query
    response = pipeline.query(
        query=test['query'],
        k=test['k'],
        chapter_filter=test.get('chapter_filter'),
        content_type_filter=test.get('content_type_filter')
    )

    # Display results
    pipeline.display_response(response)


def run_interactive_mode(pipeline: RAGPipeline) -> None:
    """Run in interactive mode with custom queries"""
    print("\n" + "=" * 80)
    print("INTERACTIVE MODE - CompTIA Security+ RAG System")
    print("=" * 80)
    print("Enter your security questions. Type 'quit' or 'exit' to stop.")
    print("You can optionally specify filters:")
    print("  - chapter:<num>  (e.g., 'chapter:1')")
    print("  - type:<video|text>  (e.g., 'type:video')")
    print("  - k:<num>  (e.g., 'k:5')")
    print("=" * 80)

    while True:
        print("\n")
        query = input("Your question: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not query:
            continue

        # Parse filters from query
        k = 3
        chapter_filter = None
        content_type_filter = None

        # Check for filter keywords
        parts = query.split()
        query_parts = []

        for part in parts:
            if part.startswith('chapter:'):
                chapter_filter = part.split(':')[1]
            elif part.startswith('type:'):
                content_type_filter = part.split(':')[1]
            elif part.startswith('k:'):
                try:
                    k = int(part.split(':')[1])
                except ValueError:
                    print(f"⚠️  Invalid k value: {part}, using default k=3")
            else:
                query_parts.append(part)

        # Reconstruct query without filters
        clean_query = ' '.join(query_parts)

        if not clean_query:
            print("⚠️  Please enter a question")
            continue

        # Run query
        try:
            response = pipeline.query(
                query=clean_query,
                k=k,
                chapter_filter=chapter_filter,
                content_type_filter=content_type_filter
            )
            pipeline.display_response(response)
        except Exception as e:
            print(f"\n❌ Error: {e}")


def run_test_suite(pipeline: RAGPipeline, tests: List[Dict]) -> None:
    """Run all test questions"""
    print("\n" + "=" * 80)
    print(f"RUNNING TEST SUITE - {len(tests)} questions")
    print("=" * 80)

    for i, test in enumerate(tests, 1):
        print(f"\n[{i}/{len(tests)}]")
        run_single_test(pipeline, test)

        if i < len(tests):
            print("\n" + "-" * 80)
            input("Press Enter to continue to next test...")

    # Print final stats
    stats = pipeline.get_usage_stats()
    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE - USAGE STATISTICS")
    print("=" * 80)
    print(f"Questions answered: {len(tests)}")
    print(f"Retrieval model: {stats['retrieval']['embedding_model']}")
    print(f"LLM model: {stats['llm']['model']}")
    print(f"Total input tokens: {stats['llm']['total_input_tokens']:,}")
    print(f"Total output tokens: {stats['llm']['total_output_tokens']:,}")
    print(f"Total cost: ${stats['llm']['total_cost']:.4f}")
    print(f"Avg cost per question: ${stats['llm']['total_cost'] / len(tests):.4f}")
    print("=" * 80)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test CompTIA Security+ RAG System")
    parser.add_argument(
        "--mode",
        type=str,
        default="interactive",
        choices=["interactive", "suite", "single"],
        help="Test mode: interactive (custom queries), suite (run all tests), single (one test)"
    )
    parser.add_argument(
        "--test-id",
        type=int,
        default=0,
        help="Test ID for single mode (0-based index)"
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Custom query for single mode"
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="Number of documents to retrieve"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        help="Filter by chapter number (e.g., '1', '2')"
    )
    parser.add_argument(
        "--content-type",
        type=str,
        choices=["video", "text"],
        help="Filter by content type"
    )

    args = parser.parse_args()

    # Initialize pipeline
    print("\n🚀 Initializing RAG Pipeline...")
    pipeline = RAGPipeline()

    # Run based on mode
    if args.mode == "interactive":
        run_interactive_mode(pipeline)

    elif args.mode == "suite":
        run_test_suite(pipeline, TEST_QUESTIONS)

    elif args.mode == "single":
        if args.query:
            # Custom query
            test = {
                "query": args.query,
                "k": args.k,
                "chapter_filter": args.chapter,
                "content_type_filter": args.content_type
            }
        else:
            # Use test from suite
            if 0 <= args.test_id < len(TEST_QUESTIONS):
                test = TEST_QUESTIONS[args.test_id]
            else:
                print(f"❌ Invalid test ID: {args.test_id}")
                print(f"Available tests: 0-{len(TEST_QUESTIONS)-1}")
                return

        run_single_test(pipeline, test)

        # Print stats
        stats = pipeline.get_usage_stats()
        print(f"\n💰 Cost: ${stats['llm']['total_cost']:.4f}")


if __name__ == "__main__":
    main()
