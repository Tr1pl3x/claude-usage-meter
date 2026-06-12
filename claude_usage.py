"""
claude-usage — a live terminal dashboard for your Claude plan limits.

Run it when you clock in and leave it open. It polls Anthropic for your
5-hour / 7-day rate-limit utilisation (the same numbers the in-app /usage
screen shows) and redraws every minute, so you never have to glance at the
Claude window again.

Stdlib only — no pip dependencies. Reads your existing Claude Code OAuth
token from ~/.claude/.credentials.json and auto-refreshes it when it expires.
"""

import json
import os
import sys
import time
import datetime
import urllib.request
import urllib.error

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
CREDS_PATH = os.path.join(os.path.expanduser("~"), ".claude", ".credentials.json")
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
REFRESH_INTERVAL = 60          # seconds between usage polls when healthy
WAIT_INTERVAL = 15             # seconds between checks while waiting for re-auth
BAR_WIDTH = 34

# Colours — 24-bit truecolor tuned to Claude's brand palette.
def _fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


RESET = "\033[0m"
BOLD = "\033[1m"

CORAL = _fg(217, 119, 87)   # #D97757 — Claude's signature accent
AMBER = _fg(224, 164, 88)   # #E0A458 — mid usage
RUST = _fg(191, 77, 67)     # #BF4D43 — high usage
CREAM = _fg(235, 230, 220)  # #EBE6DC — primary text
TAUPE = _fg(140, 134, 120)  # #8C8678 — secondary / labels
TRACK = _fg(74, 72, 64)     # #4A4840 — empty bar track

# Back-compat aliases used throughout the renderer.
DIM = TAUPE
GREY = TAUPE
CYAN = CORAL


def link(url, text):
    """Wrap text in an OSC 8 terminal hyperlink (clickable in modern terminals,
    plain text everywhere else)."""
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


# ----------------------------------------------------------------------------
# Credentials / token handling — STRICTLY READ-ONLY.
#
# Anthropic's refresh tokens are single-use: using one invalidates it and issues
# a new one. Claude Code owns that rotation. If this tool refreshed too, it would
# invalidate Claude Code's stored token and silently break its login. So we never
# refresh and never write to the credentials file — we only read the access token
# Claude Code already maintains, and re-read it each cycle to pick up its rotations.
# ----------------------------------------------------------------------------
class TokenExpired(Exception):
    """The access token has expired; only Claude Code can mint a new one."""


class NotSubscriptionLogin(Exception):
    """No subscription OAuth token present (e.g. an API-key install)."""


def load_creds():
    with open(CREDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_token(creds):
    """Return the current, unexpired access token — or raise, never refresh."""
    oauth = creds.get("claudeAiOauth")
    if not oauth or not oauth.get("accessToken"):
        raise NotSubscriptionLogin()
    expires_at = oauth.get("expiresAt", 0) / 1000
    if time.time() >= expires_at:
        raise TokenExpired()
    return oauth["accessToken"]


def fetch_usage(creds):
    """Fetch usage JSON read-only. A 401 means Claude Code must re-auth."""
    token = read_token(creds)
    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": "Bearer " + token,
        "anthropic-beta": "oauth-2025-04-20",
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise TokenExpired() from e
        raise


# ----------------------------------------------------------------------------
# Rendering helpers
# ----------------------------------------------------------------------------
def colour_for(pct):
    if pct >= 80:
        return RUST
    if pct >= 50:
        return AMBER
    return CORAL


def bar(pct):
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100 * BAR_WIDTH))
    col = colour_for(pct)
    return col + "█" * filled + TRACK + "░" * (BAR_WIDTH - filled) + RESET


def human_delta(seconds):
    seconds = int(max(0, seconds))
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s:02d}s"


def parse_reset(iso):
    dt = datetime.datetime.fromisoformat(iso)
    local = dt.astimezone()
    secs = (dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
    return local, secs


def window_lines(label, win):
    """Render a labelled window block from a {utilization, resets_at} dict."""
    if not win:
        return []
    pct = win.get("utilization") or 0.0
    line1 = f"  {CREAM}{BOLD}{label:<14}{RESET} {bar(pct)} {colour_for(pct)}{pct:>4.0f}%{RESET}"
    out = [line1]
    if win.get("resets_at"):
        local, secs = parse_reset(win["resets_at"])
        when = local.strftime("%a %d %b, %I:%M %p").lstrip("0")
        out.append(f"  {DIM}{'':<14} resets in {human_delta(secs)}  ({when}){RESET}")
    return out


def render(usage, sub_type, tier, last_update, note=""):
    lines = []
    title = f"CLAUDE USAGE"
    plan = f"{sub_type or '?'}".title()
    if tier:
        plan += f" · {tier}"
    lines.append("")
    lines.append(f"  {CORAL}{BOLD}✳ {title}{RESET}   {DIM}{plan}{RESET}")
    lines.append(f"  {GREY}{'─' * (BAR_WIDTH + 26)}{RESET}")
    lines.append("")

    lines += window_lines("5-hour", usage.get("five_hour"))
    lines.append("")
    lines += window_lines("7-day", usage.get("seven_day"))

    opus = usage.get("seven_day_opus")
    sonnet = usage.get("seven_day_sonnet")
    if opus or sonnet:
        lines.append("")
        if opus:
            lines += window_lines("7-day Opus", opus)
        if sonnet:
            lines += window_lines("7-day Sonnet", sonnet)

    extra = usage.get("extra_usage")
    if extra and extra.get("is_enabled"):
        used = extra.get("used_credits") or 0.0
        limit = extra.get("monthly_limit") or 0
        cur = extra.get("currency") or ""
        lines.append("")
        lines.append(f"  {CREAM}{BOLD}{'Extra usage':<14}{RESET} "
                     f"{CORAL}{used:,.2f}{RESET} / {limit:,} {cur} used")

    lines.append("")
    lines.append(f"  {GREY}{'─' * (BAR_WIDTH + 26)}{RESET}")
    foot = f"refreshing every {REFRESH_INTERVAL}s · last update {last_update} · Ctrl-C to quit"
    lines.append(f"  {DIM}{foot}{RESET}")
    if note:
        lines.append(f"  {AMBER}{note}{RESET}")
    lines.append(credit_line())
    lines.append("")
    return "\n".join(lines)


def credit_line():
    name = CORAL + link("https://github.com/Tr1pl3x", "Pyae Sone") + TAUPE
    credit = f"© 2026 {name} · vibecoded with my best friend Claude {CORAL}✳{TAUPE}"
    return f"  {DIM}{credit}{RESET}"


def render_message(headline, body, footer):
    """A small framed screen for non-data states (waiting for re-auth, etc.)."""
    lines = ["",
             f"  {CORAL}{BOLD}✳ CLAUDE USAGE{RESET}   {DIM}{headline}{RESET}",
             f"  {GREY}{'─' * (BAR_WIDTH + 26)}{RESET}",
             ""]
    for row in body:
        lines.append(f"  {CREAM}{row}{RESET}")
    lines += ["", f"  {GREY}{'─' * (BAR_WIDTH + 26)}{RESET}",
              f"  {DIM}{footer}{RESET}", credit_line(), ""]
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def enable_ansi():
    if os.name == "nt":
        os.system("")  # turns on VT processing in modern Windows terminals
    # Windows consoles default to cp1252, which can't render the bar glyphs.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def clear():
    sys.stdout.write("\033[2J\033[H")


def set_console_size(cols, rows):
    """Resize the console window+buffer. Works in conhost; a harmless no-op in
    Windows Terminal (which owns its own window via a pseudo-console)."""
    if os.name != "nt":
        return
    try:
        import ctypes

        class COORD(ctypes.Structure):
            _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", ctypes.c_short), ("Top", ctypes.c_short),
                        ("Right", ctypes.c_short), ("Bottom", ctypes.c_short)]

        k = ctypes.windll.kernel32
        h = k.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        # Shrink the window to a sliver first so the buffer can resize freely
        # whether we're growing or shrinking, then size buffer, then window.
        k.SetConsoleWindowInfo(h, True, ctypes.byref(SMALL_RECT(0, 0, 1, 1)))
        k.SetConsoleScreenBufferSize(h, COORD(cols, max(rows, 300)))  # keep scrollback
        k.SetConsoleWindowInfo(h, True, ctypes.byref(SMALL_RECT(0, 0, cols - 1, rows - 1)))
    except Exception:  # noqa: BLE001 — sizing is cosmetic, never fatal
        pass


def grow_console(cols, rows):
    """Pop the window in small, then expand to a snug fit — a quick launch
    flourish. Invisible (but harmless) when hosted by Windows Terminal."""
    for f in (0.34, 0.58, 0.8, 1.0):
        set_console_size(max(24, int(cols * f)), max(8, int(rows * f)))
        time.sleep(0.06)
    set_console_size(cols, rows)


def main():
    enable_ansi()
    if not os.path.exists(CREDS_PATH):
        print(f"Could not find {CREDS_PATH}.")
        print("Log in with Claude Code at least once, then run this again.")
        return 1

    note = ""
    first = True
    while True:
        interval = REFRESH_INTERVAL
        try:
            creds = load_creds()
            oauth = creds.get("claudeAiOauth", {})
            usage = fetch_usage(creds)  # raises TokenExpired / NotSubscriptionLogin
            stamp = datetime.datetime.now().strftime("%I:%M:%S %p").lstrip("0")
            frame = render(usage, oauth.get("subscriptionType"),
                           oauth.get("rateLimitTier"), stamp, note)
            note = ""
        except KeyboardInterrupt:
            clear(); print("bye 👋"); return 0
        except NotSubscriptionLogin:
            frame = render_message(
                "no subscription login",
                ["No \"Sign in with Claude\" token was found in",
                 f"{CREDS_PATH}.",
                 "",
                 "This dashboard reads the OAuth login from Claude Code",
                 "(Pro or Max). API-key installs have no plan-limit",
                 "windows to show, so there's nothing to display."],
                "Ctrl-C to quit")
        except TokenExpired:
            stamp = datetime.datetime.now().strftime("%I:%M:%S %p").lstrip("0")
            frame = render_message(
                "waiting for login",
                ["Your Claude access token has expired.",
                 "",
                 "Open Claude Code (or run any `claude` command) and this",
                 "dashboard will pick up the refreshed login automatically.",
                 "It won't touch your credentials — only Claude Code can",
                 "refresh them."],
                f"checking every {WAIT_INTERVAL}s · {stamp} · Ctrl-C to quit")
            interval = WAIT_INTERVAL
        except Exception as e:  # noqa: BLE001 — network blip etc.; keep alive
            note = f"offline — {type(e).__name__}: {e}  (retrying)"
            interval = WAIT_INTERVAL
            frame = None

        if frame is not None:
            if first:
                grow_console(68, frame.count("\n") + 2)
                first = False
            clear()
            sys.stdout.write(frame)
            sys.stdout.flush()
        else:
            sys.stdout.write("\n  " + AMBER + note + RESET + "\n")
            sys.stdout.flush()

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            clear(); print("bye 👋"); return 0


if __name__ == "__main__":
    sys.exit(main())
