# run-local.ps1 (for Windows PowerShell)
Write-Host "Starting DevDeploy locally..." -ForegroundColor Green

# Check if database is running
$dbRunning = Test-NetConnection -ComputerName localhost -Port 5432

if (-not $dbRunning.TcpTestSucceeded) {
    Write-Host "Database not found on localhost:5432" -ForegroundColor Yellow
    Write-Host "Starting Docker database..." -ForegroundColor Cyan
    docker-compose up -d db
    Start-Sleep -Seconds 5
}

Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000