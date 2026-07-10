#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$venvDir = Join-Path $projectRoot ".venv"
$uvBin = if ($env:UV_BIN) { $env:UV_BIN } else { "uv" }

if (-not (Get-Command $uvBin -ErrorAction SilentlyContinue)) {
    Write-Error "Error: 'uv' is required. Install it from https://docs.astral.sh/uv/getting-started/installation/"
}

Write-Host "============================================================"
Write-Host "Creating .venv with Python 3.12"
Write-Host "============================================================"
& $uvBin venv --python 3.12 $venvDir

$pythonBin = Join-Path $venvDir "Scripts\python.exe"
$preCommitBin = Join-Path $venvDir "Scripts\pre-commit.exe"

Write-Host ""
Write-Host "============================================================"
Write-Host "Installing raypyng[dev]"
Write-Host "============================================================"
& $uvBin pip install --python $pythonBin -e "$projectRoot[dev]"

Write-Host ""
Write-Host "============================================================"
Write-Host "Installing pre-commit hooks"
Write-Host "============================================================"
& $preCommitBin install --install-hooks

Write-Host ""
Write-Host "============================================================"
Write-Host "Done"
Write-Host "============================================================"
Write-Host "Activate with:  .\.venv\Scripts\Activate.ps1"
Write-Host "Run linters:    pre-commit run --all-files"
