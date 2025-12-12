#!/usr/bin/env python3
"""Generate weekly food trend report using Claude Sonnet 4.5."""

from datetime import datetime
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
import markdown

load_dotenv()

client = Anthropic()

SYSTEM_PROMPT = """You are "Chef Trends," a culinary intelligence analyst for upscale American country club dining.

You have access to a web_search tool. Use it to ground claims and include citations.
Rules:
- Prefer sources from the last 14 days. If you use older sources for context, label them "context (older)".
- Do not invent metrics (views, counts, "viral" claims). If a claim can't be supported by a source, mark it uncertain or omit it.
- If evidence is sparse or conflicting, say so explicitly and return fewer trends rather than guessing.
- Optimize recommendations for: photogenic plating, service practicality (country club brunch/luncheon/event execution), and "health-conscious but indulgent" positioning.

Formatting rules:
- Output MARKDOWN ONLY.
- Start with a single H1 header: "# Chef Trends — {date}".
- Use H2 headings for each trend ("## Trend Name") and put the fields as a bullet list immediately after the H2.
- Every trend must include 2–4 citations as URLs in a "Sources:" sub-bullet list."""

USER_PROMPT = """<objective>
Find 5–8 emerging food trends that fit an upscale American country club menu.
Focus on "rising" trends: recognizable on social, but not so old that they feel tired.
If you can't justify 5+ with evidence, return fewer.
</objective>

<definitions>
Emerging/rising = you can find recent evidence (last ~14 days) across at least 2 independent sources
(e.g., multiple creators/posts + a recipe/restaurant/menu mention).
Velocity labels must be evidence-based:
- Early: niche but clearly starting to replicate
- Rising: accelerating replication across creators/accounts or multiple platforms
- Peaking: mainstream coverage / big accounts, lots of copycats
- Saturated: widely commoditized, lots of SEO listicles, feels "last season"
</definitions>

<audience>
Affluent women 30–55, TikTok/Instagram/Pinterest heavy.
They want "treat yourself" indulgence with a health halo.
Country club contexts: brunch, ladies' lunch, member events.
</audience>

<constraints>
- Must be executable in a country club kitchen (no one-off lab techniques)
- Must have a "plating moment" that reads in a phone photo
- Avoid divisive extremes (super spicy challenges, prank foods, etc.)
</constraints>

<search_plan>
Do 3 passes:
1) Scan: broad "this week" / "right now" queries
2) Validate: confirm each candidate with additional sources
3) Translate: convert to a country-club dish concept + plating notes
Include a short "Search Log" section listing 6–10 queries you ran.

CRITICAL: The current year is {year}. When searching, you MUST use "{year}" in your queries, NOT any previous year. For example:
- "viral food trends December {year}" ✓
- "TikTok food trends {year}" ✓
- "restaurant trends 2024" ✗ WRONG YEAR
</search_plan>

<output_format>
# Chef Trends — {date}

## Executive Summary
- 3 bullets on what's changing this week and why it matters

## Trend 1 Name
- Platform(s):
- Velocity: Early / Rising / Peaking / Saturated (must match evidence)
- The Hook:
- Country Club Adaptation: (name the dish + 1–2 sentence description)
- Plating Notes:
- Operational Notes: (prep/service notes, allergens, labor intensity)
- Sources:
  - <URL> — what it supports (1 short clause)
  - <URL> — what it supports

(Repeat for 5–8 trends)

## Skip These
- Trend — why it's saturated/declining + 1 citation
</output_format>

Today's date is {date} (year: {year}). Prioritize the most current information you can find. Remember: use {year} in all search queries."""

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chef Trends | Weekly Culinary Intelligence</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --ivory: #FAF7F2;
            --cream: #F5F0E8;
            --charcoal: #2C2C2C;
            --charcoal-light: #4A4A4A;
            --terracotta: #C4735B;
            --terracotta-dark: #A85D47;
            --sage: #8B9B7A;
            --gold: #B8976E;
            --border: rgba(44, 44, 44, 0.1);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: 'Outfit', sans-serif;
            font-weight: 400;
            background: var(--ivory);
            color: var(--charcoal);
            line-height: 1.7;
            min-height: 100vh;
            font-size: 16px;
            -webkit-font-smoothing: antialiased;
        }}

        /* Subtle grain texture overlay */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0.03;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
            z-index: 1000;
        }}

        .header {{
            text-align: center;
            padding: 80px 24px 60px;
            border-bottom: 1px solid var(--border);
            background: linear-gradient(180deg, var(--cream) 0%, var(--ivory) 100%);
            position: relative;
        }}

        .header::after {{
            content: '';
            position: absolute;
            bottom: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: var(--terracotta);
        }}

        .masthead {{
            font-family: 'Cormorant Garamond', serif;
            font-size: clamp(3rem, 8vw, 5rem);
            font-weight: 600;
            letter-spacing: -0.02em;
            color: var(--charcoal);
            margin-bottom: 8px;
            line-height: 1.1;
        }}

        .tagline {{
            font-family: 'Outfit', sans-serif;
            font-size: 0.85rem;
            font-weight: 400;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            color: var(--charcoal-light);
            margin-bottom: 24px;
        }}

        .edition {{
            display: inline-flex;
            align-items: center;
            gap: 12px;
            font-family: 'Outfit', sans-serif;
            font-size: 0.9rem;
            color: var(--charcoal-light);
        }}

        .edition-divider {{
            width: 24px;
            height: 1px;
            background: var(--terracotta);
        }}

        .container {{
            max-width: 820px;
            margin: 0 auto;
            padding: 60px 24px 100px;
        }}

        .content {{
            animation: fadeIn 0.8s ease-out;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Typography for rendered markdown */
        .content h1 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--charcoal);
            margin: 48px 0 24px;
            letter-spacing: -0.01em;
            line-height: 1.2;
        }}

        .content h2 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--charcoal);
            margin: 56px 0 20px;
            padding-top: 48px;
            border-top: 1px solid var(--border);
            line-height: 1.3;
            position: relative;
        }}

        .content h2:first-child {{
            margin-top: 0;
            padding-top: 0;
            border-top: none;
        }}

        .content h2 strong {{
            color: var(--terracotta);
            font-weight: 600;
        }}

        .content h3 {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--charcoal);
            margin: 32px 0 16px;
        }}

        .content p {{
            margin-bottom: 20px;
            color: var(--charcoal-light);
            font-size: 1rem;
            line-height: 1.8;
        }}

        .content strong {{
            color: var(--charcoal);
            font-weight: 600;
        }}

        .content em {{
            font-style: italic;
            color: var(--charcoal);
        }}

        .content ul {{
            list-style: none;
            margin: 0 0 24px 0;
            padding: 0;
        }}

        .content ul li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 12px;
            color: var(--charcoal-light);
            line-height: 1.7;
        }}

        .content ul li::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 10px;
            width: 6px;
            height: 6px;
            background: var(--terracotta);
            border-radius: 50%;
        }}

        .content ul li strong {{
            color: var(--terracotta-dark);
            font-weight: 500;
        }}

        .content ol {{
            margin: 0 0 24px 0;
            padding-left: 24px;
        }}

        .content ol li {{
            margin-bottom: 12px;
            color: var(--charcoal-light);
            line-height: 1.7;
        }}

        .content ol li::marker {{
            color: var(--terracotta);
            font-weight: 600;
        }}

        .content hr {{
            border: none;
            height: 1px;
            background: var(--border);
            margin: 48px 0;
            position: relative;
        }}

        .content hr::after {{
            content: '\\2726';
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
            background: var(--ivory);
            padding: 0 16px;
            color: var(--terracotta);
            font-size: 1rem;
        }}

        .content a {{
            color: var(--terracotta);
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s ease;
        }}

        .content a:hover {{
            border-bottom-color: var(--terracotta);
        }}

        .content blockquote {{
            border-left: 3px solid var(--terracotta);
            padding-left: 24px;
            margin: 32px 0;
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.25rem;
            font-style: italic;
            color: var(--charcoal-light);
        }}

        .content code {{
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 0.85em;
            background: var(--cream);
            padding: 2px 8px;
            border-radius: 4px;
        }}

        /* Special styling for trend cards */
        .content h2 + ul,
        .content h2 + p + ul {{
            background: var(--cream);
            padding: 24px 24px 24px 44px;
            border-radius: 12px;
            margin: 20px 0 32px;
            border: 1px solid var(--border);
        }}

        .content h2 + ul li::before,
        .content h2 + p + ul li::before {{
            background: var(--sage);
        }}

        .footer {{
            text-align: center;
            padding: 40px 24px;
            border-top: 1px solid var(--border);
            background: var(--cream);
        }}

        .footer-text {{
            font-size: 0.8rem;
            color: var(--charcoal-light);
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }}

        .footer-logo {{
            font-family: 'Cormorant Garamond', serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--charcoal);
            margin-bottom: 8px;
        }}

        /* Responsive */
        @media (max-width: 640px) {{
            .header {{
                padding: 60px 20px 48px;
            }}

            .container {{
                padding: 40px 20px 80px;
            }}

            .content h2 {{
                font-size: 1.5rem;
                margin: 40px 0 16px;
                padding-top: 32px;
            }}

            .content h2 + ul,
            .content h2 + p + ul {{
                padding: 20px 20px 20px 40px;
            }}
        }}

        /* Print styles */
        @media print {{
            body::before {{
                display: none;
            }}

            .header {{
                padding: 40px 0;
            }}

            .content h2 {{
                break-after: avoid;
            }}
        }}
    </style>
</head>
<body>
    <header class="header">
        <h1 class="masthead">Chef Trends</h1>
        <p class="tagline">Weekly Culinary Intelligence</p>
        <div class="edition">
            <span class="edition-divider"></span>
            <span>{date} Edition</span>
            <span class="edition-divider"></span>
        </div>
    </header>

    <main class="container">
        <article class="content">
            {content}
        </article>
    </main>

    <footer class="footer">
        <div class="footer-logo">CT</div>
        <p class="footer-text">Curated for discerning palates</p>
    </footer>
</body>
</html>'''


def clean_content(text):
    """Remove any preamble text before the actual report."""
    # Find where the actual report starts (usually with --- or # heading)
    lines = text.split('\n')
    start_idx = 0

    for i, line in enumerate(lines):
        # Look for the start of the actual formatted report
        if line.strip().startswith('---') or line.strip().startswith('# '):
            start_idx = i
            break

    return '\n'.join(lines[start_idx:])


def main():
    print("Querying Claude for food trends...")
    print("(This may take 1-2 minutes with extended thinking + web search)\n")

    current_date = datetime.now().strftime("%B %d, %Y")
    current_year = datetime.now().strftime("%Y")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=16000,
        thinking={
            "type": "enabled",
            "budget_tokens": 4000
        },
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 15
        }],
        system=SYSTEM_PROMPT.format(date=current_date),
        messages=[{
            "role": "user",
            "content": USER_PROMPT.format(date=current_date, year=current_year)
        }]
    )

    # Extract text content (skip thinking blocks)
    content = ""
    for block in response.content:
        if block.type == "text":
            content += block.text

    # Clean up any preamble
    content = clean_content(content)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'smarty'])
    html_content = md.convert(content)

    # Write HTML
    docs_dir = Path(__file__).parent / "docs"
    docs_dir.mkdir(exist_ok=True)

    html = HTML_TEMPLATE.format(date=current_date, content=html_content)
    output_path = docs_dir / "index.html"
    output_path.write_text(html)

    print(f"Done! Report written to {output_path}")
    print(f"\nNext steps:")
    print(f"  git add docs/index.html")
    print(f"  git commit -m 'Update trends for {current_date}'")
    print(f"  git push")


if __name__ == "__main__":
    main()
