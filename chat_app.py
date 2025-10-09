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
    initial_sidebar_state="collapsed"
)

# Custom CSS inspired by Cluely's clean design
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Main container styling - light gradient background */
    .main {
        background: linear-gradient(135deg, #E8EEF3 0%, #D4DCE6 50%, #C8D5E3 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Chat message container - clean white cards with yellow glow */
    .stChatMessage {
        background-color: white !important;
        border-radius: 16px;
        padding: 20px 24px;
        margin: 16px 0;
        border: 2px solid rgba(251, 191, 36, 0.2);
        box-shadow: 0 0 12px rgba(251, 191, 36, 0.25), 0 2px 8px rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
    }

    .stChatMessage:hover {
        box-shadow: 0 0 20px rgba(251, 191, 36, 0.35), 0 4px 12px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
        border-color: rgba(251, 191, 36, 0.4);
    }

    /* User message styling */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, #F0F4F8 0%, #FFFFFF 100%) !important;
        border: 2px solid rgba(251, 191, 36, 0.3);
    }

    /* Assistant message styling */
    .stChatMessage[data-testid*="assistant"] {
        background-color: white !important;
        border: 2px solid rgba(251, 191, 36, 0.2);
    }

    /* Header styling - clean and minimal */
    .header-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 48px 32px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 32px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(200, 213, 227, 0.3);
    }

    .header-title {
        color: #1A202C;
        font-size: 1.8em;
        font-weight: 700;
        margin: 0 0 8px 0;
        letter-spacing: -0.02em;
    }

    .header-subtitle-main {
        color: #1A202C;
        font-size: 2.2em;
        font-weight: 700;
        margin: 8px 0;
        letter-spacing: -0.03em;
    }

    .header-subtitle {
        color: #4A5568;
        font-size: 1em;
        margin-top: 12px;
        font-weight: 400;
        letter-spacing: -0.01em;
    }

    .comptia-text {
        color: #E4002B;
        font-family: 'Inter', Arial, sans-serif;
    }

    .security-text {
        color: #1E3A8A;
    }

    /* Hide sidebar completely */
    section[data-testid="stSidebar"] {
        display: none;
    }

    /* Button styling - default blue buttons */
    .stButton>button {
        background: #5B9EFF !important;
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 0.95em;
        transition: all 0.2s ease;
        letter-spacing: 0;
        box-shadow: 0 2px 6px rgba(91, 158, 255, 0.25);
    }

    .stButton>button:hover {
        background: #4A8FEF !important;
        box-shadow: 0 4px 10px rgba(91, 158, 255, 0.35);
        transform: translateY(-2px);
    }

    /* Secondary button variant - white with yellow glow (for sample questions) */
    .main .stButton>button[kind="secondary"] {
        background: white !important;
        color: #1E293B !important;
        border: 2px solid #E2E8F0 !important;
        box-shadow: 0 0 15px rgba(251, 191, 36, 0.3), 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        font-weight: 500 !important;
    }

    .main .stButton>button[kind="secondary"]:hover {
        background: white !important;
        color: #1E293B !important;
        border-color: #FCD34D !important;
        box-shadow: 0 0 25px rgba(251, 191, 36, 0.5), 0 4px 10px rgba(0, 0, 0, 0.1) !important;
    }

    /* Metric styling */
    .metric-container {
        background: white;
        padding: 18px;
        border-radius: 12px;
        margin: 12px 0;
        border: 1px solid #E2E8F0;
        color: #334155;
        font-size: 0.9em;
        line-height: 1.8;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }

    /* Source citation styling */
    .source-box {
        background: #F8FAFC;
        padding: 16px;
        border-left: 3px solid #5B9EFF;
        border-radius: 8px;
        margin: 10px 0;
        font-size: 0.88em;
        line-height: 1.6;
        color: #475569;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .source-box strong {
        color: #1E293B;
    }

    .source-box small {
        color: #64748B;
    }

    /* Input styling - thin consistent golden border */

    /* Target the main chat input container */
    div[data-testid="stChatInput"],
    div[data-testid="stChatInput"] > div,
    .stChatInput {
        border: 2px solid rgba(251, 191, 36, 0.3) !important;
        border-radius: 20px !important;
        background: white !important;
        box-shadow: 0 0 15px rgba(251, 191, 36, 0.25) !important;
        padding: 0 !important;
    }

    /* Target all input elements inside chat input */
    div[data-testid="stChatInput"] textarea,
    div[data-testid="stChatInput"] input,
    .stChatInput textarea,
    .stChatInput input {
        border: none !important;
        border-radius: 18px !important;
        background: white !important;
        box-shadow: none !important;
        padding: 14px 20px !important;
    }

    /* Focus state - slightly brighter */
    div[data-testid="stChatInput"]:focus-within,
    .stChatInput:focus-within {
        border: 2px solid rgba(251, 191, 36, 0.4) !important;
        box-shadow: 0 0 20px rgba(251, 191, 36, 0.3) !important;
    }

    /* Override any nested divs - no extra borders */
    div[data-testid="stChatInput"] > div > div,
    .stChatInput > div,
    .stChatInput > div > div {
        border: none !important;
        box-shadow: none !important;
    }

    /* Target base-web input components - no borders */
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {
        border: none !important;
        box-shadow: none !important;
    }

    /* Text color adjustments for light theme */
    p, span, div, li {
        color: #334155;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #1E293B;
        font-weight: 600;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        color: #334155 !important;
        font-weight: 500;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .streamlit-expanderHeader:hover {
        background: #F8FAFC;
        border-color: #CBD5E1;
    }

    /* Sample question buttons - white with yellow glow */
    .main div[data-testid="column"] .stButton>button {
        background: white !important;
        color: #1E293B !important;
        border: 2px solid #E2E8F0 !important;
        box-shadow: 0 0 15px rgba(251, 191, 36, 0.3), 0 2px 6px rgba(0, 0, 0, 0.08) !important;
        font-weight: 500 !important;
    }

    .main div[data-testid="column"] .stButton>button:hover {
        background: white !important;
        border-color: #FCD34D !important;
        color: #1E293B !important;
        box-shadow: 0 0 25px rgba(251, 191, 36, 0.5), 0 4px 10px rgba(0, 0, 0, 0.1) !important;
    }

    /* Override for buttons in main content area */
    .main .stButton>button:not([kind]) {
        background: white !important;
        color: #1E293B !important;
        border: 2px solid #E2E8F0 !important;
        box-shadow: 0 0 15px rgba(251, 191, 36, 0.3), 0 2px 6px rgba(0, 0, 0, 0.08) !important;
    }

    .main .stButton>button:not([kind]):hover {
        background: white !important;
        border-color: #FCD34D !important;
        color: #1E293B !important;
        box-shadow: 0 0 25px rgba(251, 191, 36, 0.5), 0 4px 10px rgba(0, 0, 0, 0.1) !important;
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
        st.session_state.mode = 'exam'  # Always exam mode


def render_header():
    """Render the clean header without logo box"""
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">
            <span class="comptia-text">CompTIA</span>
            <span class="security-text"> Security+</span>
        </h1>
        <h2 class="header-subtitle-main">AI Study Companion</h2>
        <p class="header-subtitle">Your intelligent tutor for Security+ SY0-701 certification</p>
    </div>
    """, unsafe_allow_html=True)


# Hardcoded configuration for simplified interface
# Optimized for 2321 chunks (all 13 chapters)
DEFAULT_K = 10  # Increased from 8 to provide more context
DEFAULT_CHAPTER_FILTER = None
DEFAULT_CONTENT_TYPE_FILTER = None
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 3000


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
        with st.spinner("🤔 Retrieving and reranking documents..."):
            # Use reranking for better relevance
            # Optimized for 2321 chunks: retrieve 40 candidates, rerank to top k
            response = st.session_state.rag_pipeline.query_with_reranking(
                query=user_input,
                k=k,
                initial_k=40,  # Increased from 20 for better coverage with 2321 chunks
                chapter_filter=chapter_filter,
                content_type_filter=content_type_filter,
                reranker_model="claude-3-haiku-20240307",
                max_tokens=max_tokens,
                temperature=temperature
            )

        # Display answer
        st.markdown(response.answer)

        # Display sources
        if len(response.sources) > 0:
            with st.expander(f"📚 View {len(response.sources)} sources (reranked)"):
                for i, source in enumerate(response.sources, 1):
                    st.markdown(f"""
                    <div class="source-box">
                        <strong>Source {i}:</strong> {source.section_header}<br>
                        <small>Chapter {source.metadata.get('chapter_num')} • Relevance rank: #{i}</small><br>
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

    # Use chat mode with reranking for better accuracy on exam questions
    # Note: For exam mode, we increase k to get more context
    handle_chat_mode(user_input, min(k * 2, 7), chapter_filter, None, temperature, max_tokens)


def render_sample_questions():
    """Render sample questions as quick start buttons"""
    st.markdown("### 💡 Try these sample questions:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("What is phishing?", use_container_width=True, key="sample_q1", type="secondary"):
            return "What is phishing and what are the different types of phishing attacks?"

    with col2:
        if st.button("Explain CIA Triad", use_container_width=True, key="sample_q2", type="secondary"):
            return "Explain the CIA triad in cybersecurity"

    with col3:
        if st.button("What is a CIRT?", use_container_width=True, key="sample_q3", type="secondary"):
            return "What is a Computer Incident Response Team (CIRT) and what do they do?"

    col4, col5, col6 = st.columns(3)

    with col4:
        if st.button("Two-factor auth", use_container_width=True, key="sample_q4", type="secondary"):
            return "How does two-factor authentication work?"

    with col5:
        if st.button("DevSecOps", use_container_width=True, key="sample_q5", type="secondary"):
            return "What is DevSecOps and why is it important?"

    with col6:
        if st.button("Malware types", use_container_width=True, key="sample_q6", type="secondary"):
            return "What are the different types of malware?"

    return None


def main():
    """Main application"""
    initialize_session_state()

    # Render header
    render_header()

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
    user_input = st.chat_input("Ask me anything about CompTIA Security+...")

    # Handle sample question click
    if sample_question:
        user_input = sample_question

    # Process user input with default settings
    if user_input:
        handle_exam_mode(
            user_input,
            DEFAULT_K,
            DEFAULT_CHAPTER_FILTER,
            DEFAULT_TEMPERATURE,
            DEFAULT_MAX_TOKENS
        )
        st.rerun()


if __name__ == "__main__":
    main()
