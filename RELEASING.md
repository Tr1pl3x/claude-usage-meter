# Releasing

How to cut a new release of claude-usage. Versions follow
[SemVer](https://semver.org/): `vMAJOR.MINOR.PATCH`.

## One-time setup

Install and authenticate the GitHub CLI:

```powershell
winget install --id GitHub.cli
gh auth login          # choose GitHub.com → HTTPS → login with a browser
```

## Cutting a release

1. **Update the docs** for the new version:
   - Add a section to `CHANGELOG.md` (move items out of _Unreleased_).
   - Edit `RELEASE_NOTES.md` so it describes this release (this becomes the
     GitHub release body).
2. **Commit** those changes:
   ```powershell
   git add -A
   git commit -m "Release v1.1.0"
   git push
   ```
3. **Run the release script** with the new version:
   ```powershell
   .\release.ps1 -Version v1.1.0
   ```
   It builds a fresh `dist\claude-usage.exe`, creates and pushes the `v1.1.0`
   tag, and publishes a GitHub Release with the exe attached and the notes from
   `RELEASE_NOTES.md`. It opens the finished release in your browser at the end.

That's it. The script refuses to run if `gh` isn't authenticated, if the tag
already exists, or if you have uncommitted changes — so it's safe to re-run.

## Doing it manually (without the script)

```powershell
python -m PyInstaller --onefile --console --name claude-usage --clean claude_usage.py
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
gh release create v1.1.0 dist\claude-usage.exe --title v1.1.0 --notes-file RELEASE_NOTES.md --latest
```
