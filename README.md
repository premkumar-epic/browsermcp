# browsemcp

> Fast browser automation as a Gemini CLI extension.  
> Accessibility tree first. Screenshots only when needed. No IDE overhead.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Gemini CLI](https://img.shields.io/badge/Gemini%20CLI-Extension-blue)](https://github.com/google-gemini/gemini-cli)

---

## What is this?

browsemcp is a [Gemini CLI](https://github.com/google-gemini/gemini-cli) extension that gives Gemini a real browser to control. You describe what you want in plain English — Gemini figures out the clicks, typing, and navigation.

```
gemini> open amazon.in and find the cheapest boAt earphones under 2000

gemini> go to github trending and summarize the top 5 repos today

gemini> fill out this google form with my name Prem and email prem@gmail.com
```

### Why not just use Antigravity?

Antigravity's browser agent is slow because:
- It boots a full Electron IDE before doing anything
- It takes a screenshot every single step (expensive, slow)
- Quota runs out fast — you get ~20 minutes of heavy use

**browsemcp is different:**
- Starts in under a second (just `gemini` in your terminal)
- Uses the **accessibility tree by default** — structured text, not images, 10× cheaper per step
- You bring your own API key — no quota anxiety
- Works alongside everything else in Gemini CLI

---

## Install

### Prerequisites

- Node.js 18+
- Python 3.10+
- [Gemini CLI](https://github.com/google-gemini/gemini-cli): `npm install -g @google/gemini-cli`

### 1. Clone and install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/browsemcp
cd browsemcp
pip install -r requirements.txt
playwright install chromium
```

### 2. Install as a Gemini CLI extension

```bash
# From inside the browsemcp directory:
gemini extensions install .

# Verify it's loaded:
gemini mcp list
# Should show: browsemcp ✓
```

### 3. Use it

```bash
gemini
```

Then just talk to it naturally:

```
> search flipkart for mechanical keyboards under 3000 and tell me the top 3 results
> open hacker news and summarize the front page
> go to weather.com and tell me the forecast for Bangalore
```

---

## Available tools

| Tool | When Gemini uses it |
|---|---|
| `browser_navigate` | Go to a URL |
| `browser_snapshot` | Read the page structure (PRIMARY — fast, text-based) |
| `browser_screenshot` | See the page visually (fallback for canvas/image-heavy pages) |
| `browser_click_text` | Click by visible label — most reliable |
| `browser_click_selector` | Click by CSS selector |
| `browser_click_coordinates` | Click by x/y — last resort |
| `browser_type` | Type into a field by selector |
| `browser_type_text` | Type into a field by placeholder/label |
| `browser_key` | Press a key (Enter, Escape, Tab…) |
| `browser_scroll` | Scroll up or down |
| `browser_extract_text` | Get visible text from the page |
| `browser_go_back` | Navigate back |
| `browser_current_url` | Check current URL |
| `browser_wait` | Wait for page to load |
| `browser_close` | Close the browser |

You never call these directly — Gemini picks the right ones based on your prompt.

---

## Configuration

Set environment variables before running `gemini`:

```bash
# Run browser headlessly (no visible window)
export BROWSEMCP_HEADLESS=true

# Block images/fonts for faster page loads (breaks visual pages)
export BROWSEMCP_BLOCK_MEDIA=true
```

Or set them permanently in the extension config at `~/.gemini/extensions/browsemcp/extension.json`.

---

## How it works

browsemcp uses a **snapshot-first** strategy:

```
1. Navigate to page
2. Call browser_snapshot → returns structured accessibility tree (text, fast)
3. Gemini reads the tree, decides what to do
4. Execute action (click/type/scroll)
5. Repeat from step 2
6. Only use browser_screenshot when the page is visual/canvas-heavy
```

This is 10× cheaper per step than screenshot-based agents (Antigravity, browser-use) because:
- Accessibility tree = ~80 tokens per page
- Screenshot = ~800 tokens per page (needs vision model)

---

## Roadmap

- [ ] **v0.1** — Core MCP server (accessibility tree + screenshot fallback) ← *you are here*
- [ ] **v0.2** — Pre-built flows (amazon search, github nav, form fill, scraping)
- [ ] **v0.3** — Flow recorder (record your own reusable flows)
- [ ] **v0.4** — Session persistence (save/restore cookies and login state)
- [ ] **v0.5** — Multi-tab support

---

## Contributing

PRs welcome. This is an early project — the most useful contributions right now are:
- Bug reports on specific websites that don't work well
- New pre-built flows (in the `flows/` directory)
- Better GEMINI.md prompting strategies

---

## License

MIT
