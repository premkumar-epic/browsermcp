# browsemcp 🌐

**browsemcp** is a high-performance browser automation extension for the Gemini CLI. It provides a suite of 27 MCP tools designed for speed, reliability, and ease of use, utilizing Playwright under the hood.

## 🚀 Features

- **27 MCP Tools**: Comprehensive control over a real browser (Chromium).
- **Accessibility-First**: Uses the accessibility tree for observation, making it 10x faster and cheaper than vision-based scraping.
- **Pre-built Flows**: Specialized, high-speed tools for Amazon.in, Google Search, and GitHub Trending.
- **Flow Recorder**: Record manual browser actions once and replay them deterministically without AI latency.
- **Session Persistence**: Save login states (cookies + localStorage) to stay authenticated across tasks.
- **Developer Friendly**: Built-in health check script and a clean, modular architecture.

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/premkumar-epic/browsermcp.git
   cd browsermcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Install as Gemini CLI Extension:**
   ```bash
   gemini extensions install .
   ```

## 🛠 Usage

### Core Tools
- `browser_navigate(url)`: Go to any website.
- `browser_snapshot()`: Get the accessibility tree (primary observation tool).
- `browser_screenshot()`: Visual fallback for canvas or image-heavy sites.
- `browser_click_text(label)`: Click buttons or links by their visible text.
- `browser_type_text(label, text)`: Fill inputs by placeholder or label.

### Pre-built Flows (v0.2)
- `browser_flow_amazon_search(query)`: Get top 5 results from Amazon.in.
- `browser_flow_google_search(query)`: Fast Google search results.
- `browser_flow_github_trending()`: Today's top repositories.
- `browser_flow_fill_form(url, fields)`: Automate form filling.

### Flow Recorder (v0.3)
- `browser_record_flow(name)`: Start recording your manual actions.
- `browser_stop_recording()`: Save the recording.
- `browser_play_flow(name)`: Replay actions deterministically.

### Sessions (v0.4)
- `browser_save_session(name)`: Save your login state after manual login.
- `browser_load_session(name)`: Reuse a session to stay authenticated.

## ⚙️ Configuration

Set these environment variables in your `.env` or shell:
- `BROWSEMCP_HEADLESS`: `true` to run without a window (default: `false`).
- `BROWSEMCP_BLOCK_MEDIA`: `true` to block images/fonts for faster loading (default: `false`).

## 🧪 Development & Health Check

Run the health check script to verify your installation and any changes:
```bash
python scripts/healthcheck.py --no-browser
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
