# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chef Trend Discovery Tool - a local Python script that generates weekly food trend reports using Claude Opus 4.5 with extended thinking and web search, outputs to a static HTML page hosted on GitHub Pages.

## Architecture

- **`generate.py`** - Run locally, calls Claude API, writes `docs/index.html`
- **`docs/index.html`** - Static output, served by GitHub Pages
- **No server, no auth, no hosting costs**

## Commands

```bash
# Setup
pip install -r requirements.txt
# Create .env with ANTHROPIC_API_KEY=sk-ant-...

# Generate weekly report
python generate.py

# Deploy (after generation)
git add docs/index.html
git commit -m "Update trends"
git push
```

## Environment Variables

```
ANTHROPIC_API_KEY    # Claude API key (in .env file)
```

## Key Implementation Details

- Uses `client.messages.create()` (not streaming - simpler for local use)
- Extended thinking: `thinking={"type": "enabled", "budget_tokens": 10000}`
- Web search: `{"type": "web_search_20250305", "name": "web_search", "max_uses": 15}`
- Output: Extracts only text blocks (skips thinking blocks)
