#!/usr/bin/env python3
"""
Enhanced Chat Interface for CompTIA Security+ RAG System
Beautiful UI with logo, exam mode support, and conversation history
"""

import streamlit as st
from rag_pipeline import RAGPipeline
from exam_evaluator import ExamEvaluator, ExamQuestion
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="CompTIA Security+ AI Tutor",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Chat container */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }

    /* Header styling */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .header-title {
        color: white;
        font-size: 2.5em;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .header-subtitle {
        color: #f0f0f0;
        font-size: 1.2em;
        margin-top: 10px;
    }

    /* Logo styling */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 20px;
    }

    .comptia-logo {
        background: white;
        padding: 15px 30px;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        font-weight: bold;
        font-size: 1.8em;
    }

    .comptia-text {
        color: #E4002B;
        font-family: Arial, sans-serif;
    }

    .security-text {
        color: #1E3A8A;
        margin-left: 5px;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Metric styling */
    .metric-container {
        background: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Source citation styling */
    .source-box {
        background: #f0f4f8;
        padding: 10px;
        border-left: 4px solid #667eea;
        border-radius: 5px;
        margin: 5px 0;
        font-size: 0.9em;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'rag_pipeline' not in st.session_state:
        with st.spinner('🚀 Initializing AI Tutor...'):
            st.session_state.rag_pipeline = RAGPipeline()
    if 'exam_evaluator' not in st.session_state:
        st.session_state.exam_evaluator = None  # Lazy load when needed
    if 'mode' not in st.session_state:
        st.session_state.mode = 'chat'  # 'chat' or 'exam'


def render_header():
    """Render the beautiful header with logo"""
    st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            <div class="comptia-logo">
                <span class="comptia-text">CompTIA</span>
                <span class="security-text">Security+</span>
            </div>
        </div>
        <h1 class="header-title">AI Study Companion</h1>
        <p class="header-subtitle">Your intelligent tutor for Security+ SY0-701 certification</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar():
    """Render the sidebar with settings and info"""
    with st.sidebar:
        st.markdown("### ⚙️ Settings")

        # Mode selection
        mode = st.radio(
            "Mode",
            options=['chat', 'exam'],
            format_func=lambda x: '💬 Chat Mode' if x == 'chat' else '📝 Exam Mode',
            help="Chat Mode: Ask questions naturally. Exam Mode: Practice scenario-based questions."
        )
        st.session_state.mode = mode

        st.markdown("---")

        # Retrieval settings
        st.markdown("### 🔍 Retrieval Settings")

        k = st.slider(
            "Number of sources (k)",
            min_value=3,
            max_value=10,
            value=7 if mode == 'exam' else 3,
            help="More sources = more context but slower"
        )

        chapter_filter = st.selectbox(
            "Filter by chapter",
            options=[None, "1", "2", "3", "4"],
            format_func=lambda x: "All chapters" if x is None else f"Chapter {x}",
            help="Limit search to specific chapter"
        )

        content_type_filter = st.selectbox(
            "Content type",
            options=[None, "video", "text"],
            format_func=lambda x: "All types" if x is None else x.title(),
            help="Filter by video transcripts or text materials"
        )

        st.markdown("---")

        # LLM settings
        st.markdown("### 🤖 AI Settings")

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.1,
            help="0 = deterministic, 1 = creative"
        )

        max_tokens = st.slider(
            "Max response length",
            min_value=500,
            max_value=4000,
            value=3000 if mode == 'exam' else 2500,
            step=500
        )

        st.markdown("---")

        # Stats
        st.markdown("### 📊 Session Stats")

        stats = st.session_state.rag_pipeline.get_usage_stats()

        st.markdown(f"""
        <div class="metric-container">
            <strong>Messages:</strong> {len(st.session_state.messages) // 2}<br>
            <strong>Tokens Used:</strong> {stats['llm']['total_input_tokens'] + stats['llm']['total_output_tokens']:,}<br>
            <strong>Cost:</strong> ${stats['llm']['total_cost']:.4f}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Clear chat button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")

        # Info
        st.markdown("### ℹ️ About")
        st.info(
            "This AI tutor uses Retrieval Augmented Generation (RAG) "
            "to provide accurate answers based on CompTIA Security+ training materials. "
            "\n\n**Features:**\n"
            "- 📚 700+ training documents\n"
            "- 🧠 Chain-of-thought reasoning\n"
            "- 📝 Exam practice mode\n"
            "- 🎯 Source citations"
        )

        return k, chapter_filter, content_type_filter, temperature, max_tokens


def render_chat_message(role, content, sources=None):
    """Render a chat message with optional sources"""
    with st.chat_message(role):
        st.markdown(content)

        if sources and len(sources) > 0:
            with st.expander(f"📚 View {len(sources)} sources"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {i}:</strong> {source.section_header}<br>
                        <small>Chapter {source.metadata.get('chapter_num')} • Score: {source.score:.3f}</small><br>
                        <em>{source.summary[:150]}...</em>
                    </div>
                    """, unsafe_allow_html=True)


def handle_chat_mode(user_input, k, chapter_filter, content_type_filter, temperature, max_tokens):
    """Handle chat mode interaction"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    render_chat_message("user", user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.rag_pipeline.query(
                query=user_input,
                k=k,
                chapter_filter=chapter_filter,
                content_type_filter=content_type_filter,
                max_tokens=max_tokens,
                temperature=temperature
            )

        # Display answer
        st.markdown(response.answer)

        # Display sources
        if len(response.sources) > 0:
            with st.expander(f"📚 View {len(response.sources)} sources"):
                for i, source in enumerate(response.sources, 1):
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {i}:</strong> {source.section_header}<br>
                        <small>Chapter {source.metadata.get('chapter_num')} • Score: {source.score:.3f}</small><br>
                        <em>{source.summary[:150]}...</em>
                    </div>
                    """, unsafe_allow_html=True)

    # Add assistant message to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response.answer,
        "sources": response.sources
    })


def handle_exam_mode(user_input, k, chapter_filter, temperature, max_tokens):
    """Handle exam mode interaction"""
    st.info("📝 **Exam Mode**: Paste a complete exam question with scenario, question, and options (A, B, C, D).")

    # For now, just use chat mode with exam-style prompt
    # In future, can add structured exam question parsing
    handle_chat_mode(user_input, k, chapter_filter, None, temperature, max_tokens)


def render_sample_questions():
    """Render sample questions as quick start buttons"""
    st.markdown("### 💡 Try these sample questions:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("What is phishing?", use_container_width=True):
            return "What is phishing and what are the different types of phishing attacks?"

    with col2:
        if st.button("Explain CIA Triad", use_container_width=True):
            return "Explain the CIA triad in cybersecurity"

    with col3:
        if st.button("What is a CIRT?", use_container_width=True):
            return "What is a Computer Incident Response Team (CIRT) and what do they do?"

    col4, col5, col6 = st.columns(3)

    with col4:
        if st.button("Two-factor auth", use_container_width=True):
            return "How does two-factor authentication work?"

    with col5:
        if st.button("DevSecOps", use_container_width=True):
            return "What is DevSecOps and why is it important?"

    with col6:
        if st.button("Malware types", use_container_width=True):
            return "What are the different types of malware?"

    return None


def main():
    """Main application"""
    initialize_session_state()

    # Render header
    render_header()

    # Render sidebar and get settings
    k, chapter_filter, content_type_filter, temperature, max_tokens = render_sidebar()

    # Display chat history
    for message in st.session_state.messages:
        render_chat_message(
            message["role"],
            message["content"],
            message.get("sources")
        )

    # Show sample questions if no messages
    sample_question = None
    if len(st.session_state.messages) == 0:
        sample_question = render_sample_questions()

    # Chat input
    user_input = st.chat_input(
        "Ask me anything about CompTIA Security+..." if st.session_state.mode == 'chat'
        else "Paste your exam question here..."
    )

    # Handle sample question click
    if sample_question:
        user_input = sample_question

    # Process user input
    if user_input:
        if st.session_state.mode == 'chat':
            handle_chat_mode(user_input, k, chapter_filter, content_type_filter, temperature, max_tokens)
        else:
            handle_exam_mode(user_input, k, chapter_filter, temperature, max_tokens)

        st.rerun()


if __name__ == "__main__":
    main()
