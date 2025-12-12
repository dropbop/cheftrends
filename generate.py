#!/usr/bin/env python3
"""Generate weekly food trend report using Claude Opus 4.5."""

import os
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """You are a culinary trend analyst specializing in upscale American country club dining. You have web search capabilities—use them extensively.

When searching:
- Start with broad queries, then narrow based on what you find
- Search multiple platforms: TikTok trends, Instagram food aesthetic, Pinterest recipes
- Prioritize sources from the past 7-14 days
- If search results are sparse or conflicting, say so explicitly rather than speculating

Your client serves affluent women aged 30-55 who actively consume food content on TikTok and Instagram. They want dishes that are photogenic, on-trend, and feel special."""

USER_PROMPT = """<objective>
Find 5-8 emerging food trends that would work for an upscale country club menu. Focus on trends in the "rising" phase—viral enough to be recognized, early enough to feel novel.
</objective>

<audience>
- Affluent stay-at-home moms, 30-55
- Active on TikTok, Instagram, Pinterest
- Want Instagram-worthy dishes
- Health-conscious but indulgent ("treat yourself" mentality)
- Country club setting: brunch, ladies' luncheons, member events
</audience>

<search_guidance>
Search for:
- "viral food tiktok this week"
- "trending recipes {month} 2025"
- "food aesthetic instagram 2025"
- "pinterest food trends"
- Evolution of trends like "girl dinner", "mob wife aesthetic food", "cottage cheese recipes"
- Viral restaurant dishes being recreated at home
- Trending ingredients and flavor combinations
</search_guidance>

<output_format>
For each trend, provide:

**[Trend Name]**
- Platform: Where it's hottest (TikTok/Instagram/Pinterest)
- Velocity: Early / Rising / Peaking / Saturated
- The Hook: Why it's going viral (visual appeal, health halo, nostalgia, etc.)
- Country Club Adaptation: A specific dish concept for upscale execution
- Plating Notes: What makes it photographable
- Source: Link or reference to where you found it

End with a "Skip These" section listing 2-3 trends that are oversaturated or declining.
</output_format>

Today's date is {date}. Search for the most current information available."""

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chef Trends</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.7;
            min-height: 100vh;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 24px;
        }}
        h1 {{
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .date {{
            color: #666;
            margin-bottom: 40px;
            font-size: 14px;
        }}
        .content {{
            background: white;
            padding: 32px;
            border-radius: 16px;
            border: 1px solid #e5e5e5;
            white-space: pre-wrap;
            font-size: 15px;
        }}
        .content h2, .content strong {{
            color: #007aff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>This Week's Food Trends</h1>
        <p class="date">Generated {date}</p>
        <div class="content">{content}</div>
    </div>
</body>
</html>'''


def main():
    print("Querying Claude for food trends...")
    print("(This may take 1-2 minutes with extended thinking + web search)\n")

    current_date = datetime.now().strftime("%B %d, %Y")
    current_month = datetime.now().strftime("%B")

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 10000
        },
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 15
        }],
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(date=current_date, month=current_month)
        }]
    )

    # Extract text content (skip thinking blocks)
    content = ""
    for block in response.content:
        if block.type == "text":
            content += block.text

    # Write HTML
    docs_dir = Path(__file__).parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    html = HTML_TEMPLATE.format(date=current_date, content=content)
    output_path = docs_dir / "index.html"
    output_path.write_text(html)

    print(f"Done! Report written to {output_path}")
    print(f"\nNext steps:")
    print(f"  git add docs/index.html")
    print(f"  git commit -m 'Update trends for {current_date}'")
    print(f"  git push")


if __name__ == "__main__":
    main()
