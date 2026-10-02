# Runs the app locally without Docker (SQLite, mock Reddit/LLM).
# Usage (from the project folder):  powershell -ExecutionPolicy Bypass -File dev.ps1
# Then open http://localhost:3000

$root = $PSScriptRoot

$backend = @"
cd '$root\backend'
`$env:DATABASE_URL = 'sqlite+aiosqlite:///./dev.db'
`$env:DB_AUTO_CREATE = 'true'
.\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
"@

$frontend = @"
cd '$root\frontend'
npm run dev
"@

if (-not (Test-Path "$root\backend\.venv")) {
    Write-Host "Setting up backend (first run)..."
    python -m venv "$root\backend\.venv"
    & "$root\backend\.venv\Scripts\pip" install -r "$root\backend\requirements-dev.txt"
}
if (-not (Test-Path "$root\frontend\node_modules")) {
    Write-Host "Installing frontend packages (first run)..."
    Push-Location "$root\frontend"; npm install; Pop-Location
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontend
Write-Host "Backend:  http://localhost:8000/docs"
Write-Host "App:      http://localhost:3000  (ready in ~20s)"
