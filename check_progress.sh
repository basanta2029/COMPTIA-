#!/bin/bash
# Monitor Claude Summarization Progress

echo "=== Claude AI Summarization Progress ==="
echo ""

# Check if process is running
if pgrep -f "claude_summarizer.py" > /dev/null; then
    echo "✓ Process is running"
else
    echo "⚠ Process not running"
fi

echo ""
echo "=== Latest Output ==="
tail -30 claude_summary_output.log

echo ""
echo "=== Quick Stats ==="
grep "Chunks processed:" claude_summary_output.log 2>/dev/null | tail -1 || echo "Waiting for stats..."
grep "Total cost:" claude_summary_output.log 2>/dev/null | tail -1 || echo "Waiting for cost info..."
