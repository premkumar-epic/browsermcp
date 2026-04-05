# Contributing to browsemcp

Welcome! We're thrilled you're interested in making **browsemcp** better. Here's a guide to help you contribute effectively.

## 🛠 Setup

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/premkumar-epic/browsermcp.git
   cd browsermcp
   ```

2. **Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Install Extension:**
   ```bash
   gemini extensions install .
   ```

## 🧪 Testing

We value quality. Please ensure your changes are well-tested.

- **Run unit tests:**
  ```bash
  python tests/test_server.py
  python tests/test_flows.py
  python tests/test_sessions.py
  ```

- **Run the Pre-publish Health Check:**
  Before committing, always run:
  ```bash
  python scripts/healthcheck.py --no-browser
  ```
  This script verifies the project structure, tool registration, and security (no hardcoded keys).

## 🚀 Proposing Changes

1. **Branch Out:** Create a new branch for your feature or bug fix.
2. **Implement:** Follow existing code patterns and ensure you add docstrings to any new MCP tools.
3. **Verify:** Run all tests and the health check.
4. **Pull Request:** Submit a PR with a clear description of your changes.

## 🛡 Security

Never commit session data or hardcoded credentials. The `sessions/` directory and any JSON files in `flows/saved/` (except `.gitkeep`) are strictly ignored by Git.

## 📄 Code of Conduct

Please be respectful and professional in all interactions.

Happy coding!
