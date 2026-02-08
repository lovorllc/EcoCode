# EcoCalc Auto-Sync Script (Popravljena verzija)
# Save as auto-sync-fixed.ps1

$interval = 30   # seconds between syncs

Write-Host "Starting improved auto-sync loop..." -ForegroundColor Green

while ($true) {
    try {
        # Check if we're in a good git state
        $branch = git branch --show-current 2>$null
        if (!$branch) {
            Write-Host "Not on a branch. Fixing..." -ForegroundColor Yellow
            git checkout main 2>$null
            if ($LASTEXITCODE -ne 0) {
                git checkout -b main 2>$null
            }
        }

        # Pull latest changes (without rebase to avoid conflicts)
        Write-Host "Pulling latest changes..." -ForegroundColor Cyan
        git pull origin main --no-rebase 2>$null

        # Check for local changes
        $status = git status --porcelain 2>$null

        if ($status) {
            Write-Host "Found local changes. Syncing..." -ForegroundColor Green

            # Add all changes
            git add . 2>$null

            # Create commit with timestamp
            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            git commit -m "auto-sync $timestamp" 2>$null

            # Try to push
            git push origin main 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[$timestamp] Successfully synced!" -ForegroundColor Green
            } else {
                Write-Host "[$timestamp] Push failed. Will retry..." -ForegroundColor Yellow
            }
        } else {
            Write-Host "No changes. Repository is up to date." -ForegroundColor Gray
        }

    } catch {
        Write-Host "Error during sync: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host "Waiting $interval seconds..." -ForegroundColor Gray
    Start-Sleep -Seconds $interval
}