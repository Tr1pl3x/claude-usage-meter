# claude-usage

A live terminal dashboard for your Claude plan limits. Run it once when you
clock in, leave it on a second monitor, and stop glancing at the in-app
`/usage` screen.

It shows the same numbers Anthropic shows you:

- **5-hour window** utilisation + when it resets
- **7-day window** utilisation + reset
- Per-model weekly windows (Opus / Sonnet) when present
- Extra-usage credits

It refreshes every 60 seconds and the bars warm from coral → amber → rust as
you approach the limit.

## Requirements

- **A Claude.ai subscription login on this machine.** The tool piggybacks on
  the OAuth token Claude Code writes when you **"Sign in with Claude"**, stored
  at `%USERPROFILE%\.claude\.credentials.json`. You must have logged into Claude
  Code at least once on this machine. No separate API key or extra setup.
- **Pro *or* Max — not Max specifically.** Both tiers have the 5-hour and weekly
  limit windows this dashboard reads. The Max plan is **not** required.
- **Not for API-key users.** If you run Claude Code with an Anthropic API key
  (console / pay-as-you-go) instead of a subscription, you don't have these
  utilisation windows and this won't apply to you.
- **Windows (or Linux).** Credentials are read from a file, which works on
  Windows and Linux. On **macOS** Claude Code stores the token in the Keychain
  instead, so this file-based approach won't find it without changes.
- **No Python needed to run the exe** — only to rebuild it.

The numbers shown are *your* account's usage on *this* machine. Each
machine/person needs its own Claude Code login.

## How to use

Double-click **`dist\claude-usage.exe`** (or run it from a terminal). That's it.
Press `Ctrl-C` to quit.

No Python needed to *run* the exe. You do need to have logged into Claude Code
at least once on this machine — the tool **reads** your existing OAuth token
from `%USERPROFILE%\.claude\.credentials.json`.

### It is strictly read-only

The dashboard **never writes to your credentials and never refreshes your
login.** Anthropic's refresh tokens are single-use (each refresh invalidates the
last), and Claude Code owns that rotation — so if this tool refreshed too, it
would silently break Claude Code's login. Instead it just reads the access token
Claude Code already keeps fresh, re-reading every cycle to pick up rotations.

Access tokens last ~8 hours. As long as you use Claude Code during the day it
stays valid automatically. If it ever expires (e.g. you didn't open Claude Code
for 8h), the dashboard shows a *"waiting for login"* screen and resumes the
moment you next run any `claude` command — no restart needed.

### Tip: pin it
Right-click `claude-usage.exe` → *Send to* → *Desktop (create shortcut)* so
clocking in is a single double-click.

## Window size (pop-in-small-then-grow effect)

On launch the dashboard pops in as a small window and grows to a snug fit
around the content (~68 columns wide). How well this works depends entirely on
**which terminal hosts the exe**:

| Host | Resize behaviour |
|------|------------------|
| **Windows Console Host (conhost)** | ✅ Works — window pops in small and grows to fit. |
| **Windows Terminal** | ⚠️ Ignored — the window is owned by the terminal (via a pseudo-console), so it just appears at the current tab size. Nothing breaks; the dashboard still works. |

This is a Windows limitation, not a bug: a console program is only *allowed* to
resize its own window under conhost. Windows Terminal deliberately doesn't let
apps control its window.

### Guaranteeing the effect

To make sure the exe always runs under conhost (so the fitted/grow effect
works), set conhost as your **default terminal application**:

1. Press **Win + I** to open **Settings**.
2. Go to **Privacy & security → For developers**.
3. Scroll to **Terminal** (under the *PowerShell* / *Console* group).
4. Change the dropdown from **"Let Windows decide"** to **"Windows Console
   Host"**.

Now double-clicking `claude-usage.exe` (or any console program) launches it in
conhost, and the pop-in-and-grow animation will play every time.

> Prefer to keep Windows Terminal as your default? Leave the setting alone — the
> dashboard runs fine there too, it just skips the resize. The setting is global
> (it affects every console app), so only change it if you're happy with that.

#### Quick one-off alternative (no settings change)

If you don't want to change the global default, you can force a single launch
into conhost from Run or a command prompt:

```
conhost claude-usage.exe
```

(Use the full path to the exe if you're not in its folder.)

## Rebuilding after edits

Edit `claude_usage.py`, then run `build.bat` (needs Python on PATH). The fresh
exe lands in `dist\`.

## How it works

- `GET https://api.anthropic.com/api/oauth/usage` — the utilisation numbers
- Access token + plan info **read** from `~/.claude/.credentials.json`
  (read-only — see "It is strictly read-only" above)

Pure standard library — no third-party runtime dependencies.

## Known limitations

- **Built on undocumented internal endpoints.** The usage endpoint and
  credential format are internal to Claude Code, not a public/stable API. A
  future Claude Code update could change the endpoint, the response shape, or
  where/how the token is stored, which would stop the dashboard from working.
  This is expected — **if/when that happens, the project will be updated to
  realign with the new behaviour.** If it suddenly shows "offline" or empty
  data after a Claude Code update, check back here for a fix (or open an issue).
- **macOS isn't supported yet** — credentials live in the Keychain there, not a
  file. Windows and Linux only for now.
- **Numbers can lag by up to the refresh interval** (60s when healthy).

## Disclaimer

This is an **unofficial, community tool** and is **not affiliated with or
endorsed by Anthropic**. It relies on **undocumented internal endpoints** that
Claude Code uses, so a future Claude Code update could change or break them
without notice. It only ever reads *your own* local credentials to query *your
own* usage, and sends nothing anywhere except Anthropic's own API. Use at your
own discretion. Licensed under MIT — see `LICENSE`.
