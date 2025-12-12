import os
from datetime import datetime
from flask import Flask, request, Response, render_template_string
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-me')

auth = HTTPBasicAuth()
client = Anthropic()

users = {
    os.environ.get('ADMIN_USER', 'chef'):
        generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'changeme'))
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users[username], password):
        return username

SYSTEM_PROMPT = """You are a culinary trend analyst specializing in upscale American country club dining. You have web search capabilities—use them extensively.

When searching:
- Start with broad queries, then narrow based on what you find
- Search multiple platforms: TikTok trends, Instagram food aesthetic, Pinterest recipes
- Prioritize sources from the past 7-14 days
- If search results are sparse or conflicting, say so explicitly rather than speculating

Your client serves affluent women aged 30-55 who actively consume food content on TikTok and Instagram. They want dishes that are photogenic, on-trend, and feel special."""

USER_PROMPT_TEMPLATE = """<objective>
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
- "trending recipes [current month] 2025"
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

<optional_focus>
{user_input}
</optional_focus>

Today's date is {current_date}. Search for the most current information available."""

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chef Trends</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #fafafa;
            color: #1a1a1a;
            line-height: 1.6;
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 60px 24px;
        }
        h1 {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 40px;
        }
        .input-section {
            margin-bottom: 32px;
        }
        label {
            display: block;
            font-weight: 500;
            margin-bottom: 8px;
            color: #333;
        }
        textarea {
            width: 100%;
            padding: 16px;
            border: 1px solid #ddd;
            border-radius: 12px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            min-height: 100px;
            transition: border-color 0.2s;
        }
        textarea:focus {
            outline: none;
            border-color: #007aff;
        }
        button {
            background: #007aff;
            color: white;
            border: none;
            padding: 16px 32px;
            font-size: 17px;
            font-weight: 600;
            border-radius: 12px;
            cursor: pointer;
            transition: background 0.2s, transform 0.1s;
            width: 100%;
        }
        button:hover { background: #0066d6; }
        button:active { transform: scale(0.98); }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .output {
            margin-top: 40px;
            padding: 24px;
            background: white;
            border-radius: 16px;
            border: 1px solid #e5e5e5;
            white-space: pre-wrap;
            font-size: 15px;
            display: none;
            min-height: 200px;
        }
        .output.visible { display: block; }
        .status {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 16px;
            display: none;
        }
        .status.visible { display: block; }
        .error {
            color: #d63031;
            background: #fff5f5;
            border-color: #ffcccc;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Chef Trends</h1>
        <p class="subtitle">Discover this week's food trends for your menu</p>

        <div class="input-section">
            <label for="focus">Any specific focus? (optional)</label>
            <textarea id="focus" placeholder="e.g., planning a brunch menu, dessert trends, summer dishes..."></textarea>
        </div>

        <button id="btn" onclick="getTrends()">Find This Week's Trends</button>
        <p id="status" class="status"></p>
        <div id="output" class="output"></div>
    </div>

    <script>
        async function getTrends() {
            const btn = document.getElementById('btn');
            const output = document.getElementById('output');
            const status = document.getElementById('status');
            const focus = document.getElementById('focus').value;

            btn.disabled = true;
            btn.textContent = 'Searching...';
            output.textContent = '';
            output.classList.remove('error');
            output.classList.add('visible');
            status.classList.add('visible');
            status.classList.add('loading');
            status.textContent = 'Claude is searching the web for trends...';

            try {
                const response = await fetch('/stream', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ focus: focus })
                });

                if (!response.ok) {
                    throw new Error('Request failed');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') {
                                status.textContent = 'Complete!';
                                status.classList.remove('loading');
                            } else if (data === '[ERROR]') {
                                throw new Error('Stream error');
                            } else {
                                output.textContent += data;
                                status.textContent = 'Generating report...';
                            }
                        }
                    }
                }
            } catch (error) {
                output.textContent = 'Something went wrong. Please try again in a moment.';
                output.classList.add('error');
                status.textContent = '';
                status.classList.remove('visible');
            } finally {
                btn.disabled = false;
                btn.textContent = 'Find This Week\\'s Trends';
            }
        }
    </script>
</body>
</html>'''

@app.route('/')
@auth.login_required
def index():
    return render_template_string(TEMPLATE)

@app.route('/stream', methods=['POST'])
@auth.login_required
def stream():
    data = request.get_json() or {}
    user_focus = data.get('focus', '').strip()

    user_prompt = USER_PROMPT_TEMPLATE.format(
        user_input=user_focus or "No specific focus—give a general trend overview.",
        current_date=datetime.now().strftime("%B %d, %Y")
    )

    def generate():
        try:
            with client.messages.stream(
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
                messages=[{"role": "user", "content": user_prompt}]
            ) as stream:
                for event in stream:
                    if hasattr(event, 'delta'):
                        if event.delta.type == "text_delta":
                            yield f"data: {event.delta.text}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            app.logger.error(f"Stream error: {e}")
            yield "data: [ERROR]\n\n"

    response = Response(generate(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

if __name__ == '__main__':
    app.run(debug=True)
