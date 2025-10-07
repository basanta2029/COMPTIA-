#!/usr/bin/env python3
"""
Streamlit UI for CompTIA Security+ RAG System
Interactive chat interface for Q&A
"""

import streamlit as st
from rag_pipeline import RAGPipeline, RAGResponse
from typing import Optional, List
import time


# Page config
st.set_page_config(
    page_title="CompTIA Security+ RAG",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def initialize_pipeline():
    """Initialize RAG pipeline (cached)"""
    with st.spinner("🚀 Initializing RAG Pipeline..."):
        pipeline = RAGPipeline()
    return pipeline


def display_source_card(source, index: int):
    """Display a source document as a card"""
    with st.expander(f"📄 Source {index + 1}: {source.section_header} (Score: {source.score:.4f})"):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.markdown("**Metadata**")
            st.write(f"**Chunk ID:** `{source.chunk_id}`")
            st.write(f"**Chapter:** {source.metadata.get('chapter_num', 'N/A')}")
            st.write(f"**Section:** {source.metadata.get('section_num', 'N/A')}")
            st.write(f"**Type:** {source.metadata.get('content_type', 'N/A')}")
            st.write(f"**Score:** {source.score:.4f}")

        with col2:
            st.markdown("**Summary**")
            st.info(source.summary)

            st.markdown("**Full Content**")
            with st.container():
                st.text_area(
                    "Content",
                    source.content,
                    height=200,
                    key=f"content_{source.chunk_id}",
                    label_visibility="collapsed"
                )


def main():
    """Main Streamlit app"""

    # Title and description
    st.title("🔒 CompTIA Security+ RAG System")
    st.markdown("Ask questions about CompTIA Security+ certification topics")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Filters
        st.subheader("Filters")
        chapter_filter = st.selectbox(
            "Chapter",
            options=["All", "1", "2", "3", "4"],
            index=0
        )

        content_type_filter = st.selectbox(
            "Content Type",
            options=["All", "Video", "Text"],
            index=0
        )

        # Retrieval settings
        st.subheader("Retrieval")
        k = st.slider(
            "Number of documents (k)",
            min_value=1,
            max_value=10,
            value=3,
            help="How many relevant documents to retrieve"
        )

        # LLM settings
        st.subheader("LLM Generation")
        max_tokens = st.slider(
            "Max tokens",
            min_value=500,
            max_value=4000,
            value=2500,
            step=100,
            help="Maximum length of generated answer"
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="Higher = more creative, Lower = more deterministic"
        )

        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

        # Info
        st.divider()
        st.markdown("### 📊 About")
        st.markdown("""
        This RAG system uses:
        - **OpenAI** embeddings (text-embedding-3-small)
        - **Qdrant** vector database
        - **Claude Sonnet 4** for answers
        - **Summary-indexed retrieval** for better context
        """)

    # Initialize pipeline
    try:
        pipeline = initialize_pipeline()
    except Exception as e:
        st.error(f"❌ Failed to initialize pipeline: {e}")
        st.stop()

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Display sources if available
            if "sources" in message:
                st.divider()
                st.markdown("**📚 Sources**")
                for i, source in enumerate(message["sources"]):
                    display_source_card(source, i)

    # Chat input
    if prompt := st.chat_input("Ask a security question..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            # Create placeholders
            response_placeholder = st.empty()
            sources_placeholder = st.empty()

            # Show loading
            with response_placeholder:
                with st.spinner("🤔 Thinking..."):
                    start_time = time.time()

                    # Convert filter values
                    chapter = None if chapter_filter == "All" else chapter_filter
                    content_type = None if content_type_filter == "All" else content_type_filter.lower()

                    try:
                        # Run query
                        response: RAGResponse = pipeline.query(
                            query=prompt,
                            k=k,
                            chapter_filter=chapter,
                            content_type_filter=content_type,
                            max_tokens=max_tokens,
                            temperature=temperature
                        )

                        elapsed_time = time.time() - start_time

                        # Display answer
                        st.markdown(response.answer)

                        # Display metadata
                        st.caption(f"⏱️ Response time: {elapsed_time:.2f}s | 📄 Sources: {response.num_sources}")

                        # Display sources
                        with sources_placeholder:
                            st.divider()
                            st.markdown("**📚 Sources**")
                            for i, source in enumerate(response.sources):
                                display_source_card(source, i)

                        # Add assistant message to chat history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response.answer,
                            "sources": response.sources
                        })

                    except Exception as e:
                        response_placeholder.error(f"❌ Error: {str(e)}")

    # Sample questions
    st.divider()
    st.markdown("### 💡 Sample Questions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("What is phishing?"):
            st.session_state.sample_query = "What is phishing?"
            st.rerun()

    with col2:
        if st.button("Explain two-factor authentication"):
            st.session_state.sample_query = "Explain two-factor authentication"
            st.rerun()

    with col3:
        if st.button("What is the CIA triad?"):
            st.session_state.sample_query = "What is the CIA triad?"
            st.rerun()

    # Handle sample query
    if "sample_query" in st.session_state:
        query = st.session_state.sample_query
        del st.session_state.sample_query

        # Add to messages and rerun to trigger chat input
        st.session_state.messages.append({"role": "user", "content": query})
        st.rerun()


if __name__ == "__main__":
    main()
