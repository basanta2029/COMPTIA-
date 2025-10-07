# CompTIA Security+ Chat Interface

## Beautiful, Modern UI with Enhanced Exam Support

A sleek chat interface for the CompTIA Security+ RAG system with:

- 🎨 Beautiful gradient UI with CompTIA Security+ branding
- 💬 Real-time chat with conversation history
- 📝 Exam mode for scenario-based practice questions
- 📚 Source citations with expandable references
- ⚙️ Configurable retrieval and AI settings
- 📊 Live session statistics

## Features

### 1. Professional CompTIA Branding
- Official CompTIA Security+ logo styling
- Red "CompTIA" text + Blue "Security+" text
- Clean, professional design with gradient backgrounds

### 2. Dual Modes
- **Chat Mode** 💬: Natural Q&A for learning
- **Exam Mode** 📝: Practice scenario-based questions

### 3. Smart Settings
- Retrieval depth (k=3-10)
- Chapter filtering (1-4)
- Content type filtering (video/text)
- AI temperature control
- Response length adjustment

### 4. Quick Start Samples
Six pre-loaded sample questions:
- What is phishing?
- Explain CIA Triad
- What is a CIRT?
- Two-factor authentication
- DevSecOps
- Malware types

### 5. Source Citations
Every answer includes:
- Number of source documents used
- Document titles and chapter numbers
- Relevance scores
- Document summaries

## Usage

### Start the Chat Interface

```bash
# Run on default port 8501
streamlit run chat_app.py

# Or specify custom port
streamlit run chat_app.py --server.port 8502
```

Then open: http://localhost:8502

### Chat Mode

1. Select **💬 Chat Mode** in sidebar
2. Type your question or click a sample question
3. Get instant answers with source citations
4. Adjust settings for different retrieval strategies

### Exam Mode

1. Select **📝 Exam Mode** in sidebar
2. Paste a complete exam question with:
   - Scenario
   - Question
   - Options (A, B, C, D)
3. System uses enhanced reasoning to select best answer
4. Get detailed chain-of-thought explanation

## UI Highlights

### Header
```
╔══════════════════════════════════════╗
║     [CompTIA Security+]              ║
║                                      ║
║    AI Study Companion                ║
║ Your intelligent tutor for Security+ ║
╚══════════════════════════════════════╝
```

### Sidebar Sections
1. ⚙️ **Settings**
   - Mode toggle (Chat/Exam)

2. 🔍 **Retrieval Settings**
   - Number of sources (k)
   - Chapter filter
   - Content type filter

3. 🤖 **AI Settings**
   - Temperature
   - Max response length

4. 📊 **Session Stats**
   - Message count
   - Tokens used
   - Cost tracking

5. 🗑️ **Clear History**
   - Reset conversation

6. ℹ️ **About**
   - System information

### Chat Interface
- User messages: Right-aligned with user avatar
- AI responses: Left-aligned with assistant avatar
- Expandable source citations
- Smooth scrolling
- Real-time typing indicators

## Design Specifications

### Colors
- **Primary Gradient**: `#667eea` → `#764ba2` (purple gradient)
- **CompTIA Red**: `#E4002B`
- **Security+ Blue**: `#1E3A8A`
- **Background**: White with gradient overlay
- **Source Boxes**: `#f0f4f8` with purple accent

### Typography
- **Headers**: Bold, 2.5em, white with shadow
- **Logo**: Bold, 1.8em, red and blue
- **Body**: Standard Streamlit defaults
- **Sources**: 0.9em with italic summaries

### Components
- **Rounded corners**: 10-20px border radius
- **Box shadows**: Subtle depth with rgba(0,0,0,0.1-0.2)
- **Hover effects**: Button lift with shadow increase
- **Transitions**: Smooth 0.3s animations

## Architecture

```
chat_app.py
    ├── Header (logo + title)
    ├── Sidebar (settings)
    │   ├── Mode selection
    │   ├── Retrieval settings
    │   ├── AI settings
    │   ├── Session stats
    │   └── Clear button
    ├── Chat History
    │   ├── User messages
    │   └── AI responses with sources
    ├── Sample Questions (if empty)
    └── Chat Input
```

## Session State Management

Persistent data across reruns:
- `messages`: Conversation history
- `rag_pipeline`: Initialized RAG system
- `exam_evaluator`: Lazy-loaded exam evaluator
- `mode`: Current mode (chat/exam)

## Performance

- **Initial Load**: ~2-3 seconds (RAG initialization)
- **First Query**: ~3-5 seconds (retrieval + generation)
- **Subsequent Queries**: ~2-4 seconds
- **Cost**: ~$0.01-0.03 per question (depending on k and length)

## Screenshots

### Main Interface
```
┌──────────────────────────────────────────────────────┐
│  [CompTIA Security+]                                 │
│  AI Study Companion                                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  💡 Try these sample questions:                     │
│  [What is phishing?] [CIA Triad] [What is CIRT?]   │
│                                                      │
│  👤 User: What is phishing?                         │
│                                                      │
│  🤖 Assistant: Phishing is a social engineering...  │
│     📚 View 3 sources ▼                             │
│                                                      │
│  [Ask me anything about CompTIA Security+...]      │
└──────────────────────────────────────────────────────┘
```

## Customization

### Change Logo Colors
Edit the CSS in `chat_app.py`:
```python
.comptia-text {
    color: #E4002B;  # CompTIA red
}
.security-text {
    color: #1E3A8A;  # Security+ blue
}
```

### Adjust Gradient
```python
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Modify Default Settings
In `render_sidebar()`:
```python
k = st.slider("Number of sources", value=5)  # Change default
temperature = st.slider("Temperature", value=0.2)  # Change default
```

## Comparison with Original app.py

| Feature | Original app.py | New chat_app.py |
|---------|----------------|-----------------|
| UI Design | Basic Streamlit | Custom gradient + CompTIA branding |
| Logo | None | Official CompTIA Security+ styling |
| Sample Questions | None | 6 pre-loaded samples |
| Source Display | Basic expander | Styled boxes with metadata |
| Session Stats | None | Live token/cost tracking |
| Exam Mode | Basic | Enhanced with mode toggle |
| Chat History | Limited | Full persistent history |

## Future Enhancements

- [ ] Add exam question parser in exam mode
- [ ] Voice input for questions
- [ ] PDF export of chat history
- [ ] Bookmarking favorite Q&As
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Progress tracking across sessions

---

**Status**: Production-ready ✅

**URL**: http://localhost:8502 (when running)

**Perfect for**: Study sessions, exam prep, quick reference
