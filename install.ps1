#!/usr/bin/env pwsh
# ============================================================
# Content Crew Studio — Windows Install & Run Script
# ============================================================
# Usage:
#   .\install.ps1          — install dependencies + run app
#   .\install.ps1 -RunOnly — skip install, just run the app
# ============================================================

param(
    [switch]$RunOnly
)

$ErrorActionPreference = "Stop"

# ── Find a compatible Python (3.10 – 3.13) ─────────────────
$python = $null
foreach ($candidate in @("python3.12-64.exe", "python3.12.exe", "python3.11-64.exe", "python3.11.exe", "python3.10-64.exe", "python3.10.exe")) {
    try {
        $ver = & $candidate --version 2>&1
        if ($ver -match "Python 3\.(1[0-3])") {
            $python = $candidate
            Write-Host "Using: $python ($ver)" -ForegroundColor Green
            break
        }
    } catch { }
}

if (-not $python) {
    Write-Host "No compatible Python (3.10-3.13) found on PATH." -ForegroundColor Red
    Write-Host "Download Python 3.12 from https://python.org and add it to PATH." -ForegroundColor Yellow
    exit 1
}

# ── Install dependencies (skip if -RunOnly) ─────────────────
if (-not $RunOnly) {
    Write-Host "`nInstalling dependencies..." -ForegroundColor Cyan
    & $python -m pip install --prefer-binary -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nInstall failed. See error above." -ForegroundColor Red
        exit 1
    }
    Write-Host "`nAll dependencies installed!" -ForegroundColor Green
}

# ── Launch app ───────────────────────────────────────────────
Write-Host "`nStarting Content Crew Studio at http://localhost:8501`n" -ForegroundColor Cyan
& $python -m streamlit run streamlit_app.py --server.port 8501
