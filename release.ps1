<#
.SYNOPSIS
  Cut a new release: build the exe, tag the version, and publish a GitHub
  Release with the exe attached. Requires the GitHub CLI (`gh`), authenticated.

.EXAMPLE
  .\release.ps1 -Version v1.1.0
  .\release.ps1 v1.1.0 -Notes "Custom one-off notes"

.NOTES
  - Update CHANGELOG.md and RELEASE_NOTES.md before running.
  - By default the release body comes from RELEASE_NOTES.md.
#>
param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Version,
  [string]$Notes
)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# 1. Validate inputs and tooling -------------------------------------------------
if ($Version -notmatch '^v\d+\.\d+\.\d+$') {
  Fail "Version must look like v1.2.3 (got '$Version')."
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  Fail "GitHub CLI 'gh' not found. Install it, then run: gh auth login"
}
gh auth status 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "gh is not authenticated. Run: gh auth login" }
if (git tag --list $Version) { Fail "Tag $Version already exists." }
if (git status --porcelain) {
  Fail "You have uncommitted changes. Commit them first (CHANGELOG/notes included)."
}

# 2. Build a fresh single-file exe ----------------------------------------------
Write-Host "==> Stopping any running dashboard so the exe can be overwritten..." -ForegroundColor Cyan
Stop-Process -Name claude-usage -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 400

Write-Host "==> Building claude-usage.exe ..." -ForegroundColor Cyan
python -m PyInstaller --onefile --console --name claude-usage --clean claude_usage.py
if ($LASTEXITCODE -ne 0) { Fail "PyInstaller build failed." }
if (-not (Test-Path 'dist\claude-usage.exe')) { Fail "Build did not produce dist\claude-usage.exe." }

# 3. Tag and push ----------------------------------------------------------------
Write-Host "==> Tagging $Version and pushing ..." -ForegroundColor Cyan
git tag -a $Version -m "$Version"
git push origin $Version
if ($LASTEXITCODE -ne 0) { Fail "Pushing the tag failed." }

# 4. Publish the GitHub Release --------------------------------------------------
Write-Host "==> Creating GitHub release $Version ..." -ForegroundColor Cyan
$ghArgs = @('release', 'create', $Version, 'dist\claude-usage.exe',
            '--title', "$Version", '--latest')
if ($Notes) {
  $ghArgs += @('--notes', $Notes)
} elseif (Test-Path 'RELEASE_NOTES.md') {
  $ghArgs += @('--notes-file', 'RELEASE_NOTES.md')
} else {
  $ghArgs += '--generate-notes'
}
gh @ghArgs
if ($LASTEXITCODE -ne 0) { Fail "gh release create failed." }

Write-Host ""
Write-Host "Done! Release $Version is live with claude-usage.exe attached." -ForegroundColor Green
gh release view $Version --web
