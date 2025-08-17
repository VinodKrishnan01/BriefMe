<#
.SYNOPSIS
  One-shot dev startup for Brief Generator (Windows PowerShell).
.DESCRIPTION
  - Ensures Python venv and installs server requirements
  - Installs client node modules
  - Starts Flask server and React client in separate PowerShell windows
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Section($text) {
  Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Ensure-Cmd($name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "Required command '$name' not found in PATH. Please install it."
  }
}

# Resolve repo paths
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ClientDir = Join-Path $Root 'client'
$ServerDir = Join-Path $Root 'server'
$VenvDir   = Join-Path $ServerDir 'venv'
$VenvPy    = Join-Path $VenvDir 'Scripts/python.exe'
$VenvPip   = Join-Path $VenvDir 'Scripts/pip.exe'

Write-Section 'Pre-flight checks'
Ensure-Cmd 'python'
Ensure-Cmd 'npm'
Ensure-Cmd 'node'

# --- Python setup ---
Write-Section 'Python environment setup'
if (-not (Test-Path $VenvPy)) {
  Write-Host 'Creating virtual environment...' -ForegroundColor Yellow
  & python -m venv $VenvDir
}

Write-Host 'Installing server requirements (pip)...' -ForegroundColor Yellow
& $VenvPip install --upgrade pip | Out-Host
& $VenvPip install -r (Join-Path $ServerDir 'requirements.txt') | Out-Host

# --- Node setup ---
Write-Section 'Node modules setup'
Push-Location $ClientDir
try {
  if (Test-Path (Join-Path $ClientDir 'package-lock.json')) {
    Write-Host 'Installing client dependencies (npm ci)...' -ForegroundColor Yellow
    npm ci | Out-Host
  } else {
    Write-Host 'Installing client dependencies (npm install)...' -ForegroundColor Yellow
    npm install | Out-Host
  }
}
finally {
  Pop-Location
}

# --- Launch processes ---
Write-Section 'Starting services'

# Start Flask server in a new PowerShell window and keep it open
$serverCmd = "cd '$ServerDir'; & '$VenvPy' app.py"
Start-Process -FilePath powershell -ArgumentList "-NoExit","-Command", $serverCmd -WorkingDirectory $ServerDir

# Start React client in a new PowerShell window and keep it open
$clientCmd = "cd '$ClientDir'; npm start"
Start-Process -FilePath powershell -ArgumentList "-NoExit","-Command", $clientCmd -WorkingDirectory $ClientDir

Write-Host "`nAll set!" -ForegroundColor Green
Write-Host "Server:  http://localhost:5000 (health at /health)" -ForegroundColor Green
Write-Host "Client:  http://localhost:3000" -ForegroundColor Green
Write-Host "Two PowerShell windows were opened for server and client logs." -ForegroundColor Green
