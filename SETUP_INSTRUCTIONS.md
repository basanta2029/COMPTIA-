# Setup Instructions for Claude AI Summarization

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `anthropic` - Claude API client
- `tqdm` - Progress bars
- `python-dotenv` - Environment variable management

### 2. Add Your API Key

**Option A: Using .env file (Recommended)**

Edit the `.env` file in the project root:

```bash
# Open .env file
nano .env

# Replace 'your-api-key-here' with your actual key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx...
```

**Option B: Environment Variable**

```bash
export ANTHROPIC_API_KEY='sk-ant-api03-xxxxx...'
```

**Where to get your API key:**
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy and paste it into `.env` file

### 3. Test the Setup

Run a dry run to test (processes 5 chunks, doesn't save):

```bash
python3 claude_summarizer.py --dry-run --max-chunks 5
```

You should see:
- Progress bar
- Token usage
- Cost estimate
- Sample summaries

### 4. Run Full Summarization

Once you're happy with the test results:

```bash
# Process all 701 chunks
python3 claude_summarizer.py
```

**Note:** This will:
- Process ~701 chunks across 112 documents
- Cost approximately **$0.95**
- Take ~15-20 minutes (rate limiting)
- Update summaries in place
- Create `ai_summary_report.json`

## Usage Options

### Process Specific Chapter Only

```bash
# Just chapter 1
python3 claude_summarizer.py --chapter 01

# Just chapter 3
python3 claude_summarizer.py --chapter 03
```

### Test with Limited Chunks

```bash
# Process only 10 chunks
python3 claude_summarizer.py --max-chunks 10
```

### Dry Run (Test Without Saving)

```bash
# See what happens without making changes
python3 claude_summarizer.py --dry-run --max-chunks 5
```

## Safety Features

✅ **Automatic Backup**: `data_clean_backup/` created before running
✅ **Dry Run Mode**: Test before committing
✅ **Error Handling**: Keeps old summary if AI fails
✅ **.env Ignored**: API key never committed to git

## Troubleshooting

### Error: ANTHROPIC_API_KEY not found

```bash
# Check if .env file exists
ls -la .env

# Verify it has your key
cat .env

# Make sure python-dotenv is installed
pip install python-dotenv
```

### Error: ModuleNotFoundError: No module named 'anthropic'

```bash
# Install dependencies
pip install -r requirements.txt
```

### Rate Limit Errors

The script already includes rate limiting (50 req/sec). If you still hit limits:
- Wait a few minutes
- The script will continue from where it stopped
- Already-processed files are skipped

## File Structure

```
CompTia/
├── .env                          # Your API key (NOT in git)
├── requirements.txt              # Dependencies
├── claude_summarizer.py         # Main script
├── data_clean/                   # Updated with AI summaries
├── data_clean_backup/            # Original summaries (backup)
└── ai_summary_report.json       # Generated after run
```

## Cost Breakdown

| Item | Calculation | Estimated Cost |
|------|-------------|----------------|
| Input | 701 chunks × ~200 tokens × $0.003/1K | $0.42 |
| Output | 701 chunks × ~50 tokens × $0.015/1K | $0.53 |
| **Total** | | **~$0.95** |

Actual cost will be in the `ai_summary_report.json` after running.

## Next Steps

After generating AI summaries:

1. **Validate Quality**: Check `ai_summary_report.json`
2. **Compare Samples**: Look at a few summaries vs original
3. **Generate Embeddings**: Use summaries for vector DB
4. **Build RAG System**: Implement retrieval with Claude

## Support

- Anthropic API Docs: https://docs.anthropic.com/
- Claude Console: https://console.anthropic.com/
- Get API Key: https://console.anthropic.com/settings/keys
