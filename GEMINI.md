# browsemcp — Browser Agent Skill

You have access to a real web browser through the `browsemcp` MCP server.
Use it whenever the user asks you to browse, search, click, fill forms, scrape, or automate anything on the web.

## Decision Tree — which tool to call

```
New page / after navigation?
  → browser_snapshot  (always start here)

Need to click something?
  → browser_click_text("visible label")  ← try first
  → browser_click_selector("#id or .class")  ← if you have a clear selector
  → browser_click_coordinates(x, y)  ← last resort, use x/y from snapshot

Need to type?
  → browser_type_text("placeholder text", "value")  ← easiest
  → browser_type("css selector", "value")  ← if you know the selector

Page has visual content (charts, images, canvas)?
  → browser_screenshot  ← only then

Done with the task?
  → browser_close
```

## Speed rules

1. **Never screenshot when snapshot is enough.** Snapshot = text, fast, cheap. Screenshot = image, slow, expensive.
2. **One snapshot per page.** Don't call snapshot twice on the same page unless you've done an action.
3. **Chain actions tightly.** navigate → snapshot → click → snapshot → extract. Don't add extra waits unless the page is slow.
4. **For search tasks:** navigate to site → snapshot → type in search box → Enter → snapshot → extract_text
5. **For form fill tasks:** snapshot to find field names → type_text for each field → click submit

## Common patterns

### Search something
```
browser_navigate("site.com")
browser_snapshot()  # find the search input
browser_type_text("Search", "your query")
browser_key("Enter")
browser_snapshot()  # see results
browser_extract_text(".results")
```

### Click a button
```
browser_snapshot()  # find the button label
browser_click_text("Add to Cart")
browser_snapshot()  # confirm action worked
```

### Fill a form
```
browser_navigate("form url")
browser_snapshot()  # see all fields
browser_type_text("First Name", "Prem")
browser_type_text("Email", "prem@example.com")
browser_click_text("Submit")
```

## Flow Tools (v0.2)

For common tasks, **always prefer flow tools** over raw browser tools. They use specialized logic, are significantly faster, and skip the observe→think→act loop.

- `browser_flow_amazon_search(query)`
- `browser_flow_github_trending()`
- `browser_flow_google_search(query)`
- `browser_flow_fill_form(url, fields)`

## Flow Recorder (v0.3)

**Flow Recorder — record once, replay instantly.** Use `browser_record_flow` to capture a task, and `browser_play_flow` to repeat it without any AI reasoning. This is perfect for repetitive workflows, logging into internal systems, or complex multi-step scraping.

1. **Record:** Call `browser_record_flow(name="login")`. A browser window opens. Perform the task manually.
2. **Stop:** Call `browser_stop_recording()`. The steps are saved to `flows/saved/login.json`.
3. **Replay:** Call `browser_play_flow("login")`. It will replay your exact actions deterministically.

## Sessions (v0.4)

**Sessions — save your login state once, reuse it forever.** Use `browser_save_session` after logging in manually, then `browser_load_session` at the start of any task that needs authentication. This prevents you from having to log in every time or deal with 2FA repeatedly.

1. **Login Manually:** Use `browser_navigate` and `browser_type` to log in.
2. **Save Session:** Call `browser_save_session(name="github")`.
3. **Reuse Session:** In a new chat, call `browser_load_session("github")` before navigating to GitHub.

## Error handling

- If `browser_click_text` fails → try `browser_click_selector` with id/class from snapshot
- If selector fails → use `browser_click_coordinates` with x/y from snapshot
- If page seems stuck → `browser_wait(2000)` then `browser_snapshot`
- If you need to go back → `browser_go_back`

## Environment variables (user can set these)

| Variable | Default | Effect |
|---|---|---|
| `BROWSEMCP_HEADLESS` | `false` | Run browser headlessly (no window) |
| `BROWSEMCP_BLOCK_MEDIA` | `false` | Block images/fonts for faster loads |
