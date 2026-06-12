A live terminal dashboard for your Claude plan limits — run it once when you
clock in and never glance at the in-app /usage screen again.

### What's new in v1.0.3
- **Live countdowns.** The "resets in" timers now tick down every second
  (`H:MM:SS`), so you can watch your window approach in real time.
- **Fewer rate-limit (429) hiccups.** The default poll interval is now 120s
  (matching Anthropic's own usage screen), so the API rate-limits far less often.
- **Tunable interval.** Poll slower if you like: `claude-usage.exe 180`, or set
  the `CLAUDE_USAGE_INTERVAL` environment variable. Minimum 30s.
- Simplified footer.

_(Earlier 1.0.x releases added automatic back-off for rate limits, a clean
single-screen error state, the correct extra-usage amount, and a version in the
footer.)_

### Download
Grab **claude-usage.exe** below and double-click it. No Python or install needed.

### Requirements
- Logged into **Claude Code** with a **Claude Pro or Max** subscription on this
  machine (it reads the OAuth token Claude Code already stores).
- Windows. (macOS keeps the token in Keychain — not supported yet.)

### What it shows
- 5-hour and weekly (7-day) usage with live, colour-coded bars
- Live reset countdowns and extra-usage credits
- Fetches every 120s; strictly **read-only** — never touches your login

See the README for details and known limitations.
