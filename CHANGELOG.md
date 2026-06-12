# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/), and this project
uses [Semantic Versioning](https://semver.org/) (`vMAJOR.MINOR.PATCH`).

## [Unreleased]

_Nothing yet._

## [1.0.1] — 2026-06-12

### Fixed
- **Rate-limit handling.** A single 429 from the usage API used to trigger a
  15s retry storm that piled up scrolling "offline" lines and never recovered.
  Now every state (including errors) redraws one cleared screen, and network/429
  failures back off exponentially (60→120→240→300s, honouring `Retry-After`).
- Raised the healthy poll interval from 60s to 90s to stay well under the API's
  rate limit.
- **Extra-usage amount.** The API reports money in minor units (cents), so the
  monthly limit now shows as `155.00 AUD` instead of `15,500`.

## [1.0.0] — 2026-06-12

First public release.

### Added
- Live terminal dashboard for Claude plan limits: 5-hour and weekly (7-day)
  utilisation with colour-coded bars, reset countdowns, and extra-usage credits.
- Auto-refreshing display (every 60s) with a Claude-branded coral/amber/rust
  theme and a clickable author credit footer.
- Single-file Windows executable built with PyInstaller (`build.bat`).
- Fitted pop-in window sizing (works under the classic console host).

### Behaviour / safety
- **Strictly read-only**: reads the access token Claude Code maintains and never
  writes to or refreshes credentials. (Verified that Anthropic's refresh tokens
  are single-use, so refreshing would break Claude Code's login.)
- Graceful "waiting for login" screen on token expiry that auto-recovers when
  Claude Code next refreshes; "no subscription login" screen for API-key setups.

### Fixed
- Disabled conhost QuickEdit mode so a click no longer freezes the dashboard.
- Hid the idle terminal cursor while running (restored on exit).

[Unreleased]: https://github.com/Tr1pl3x/claude-usage-meter/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/Tr1pl3x/claude-usage-meter/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Tr1pl3x/claude-usage-meter/releases/tag/v1.0.0
