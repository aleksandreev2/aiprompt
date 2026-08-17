Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "[NovelAI Prompt Lab] Starting local UI..."
Write-Host "[NovelAI Prompt Lab] LM Studio is optional at startup and may be opened later."

if (!(Test-Path ".venv")) {
    Write-Host "[NovelAI Prompt Lab] Creating virtual environment..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& .\.venv\Scripts\Activate.ps1

python -c "import gradio,httpx,pydantic,dotenv" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[NovelAI Prompt Lab] Installing dependencies (first launch only)..."
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

python app.py
