# Jednostavna sinhronizacija - pokreni ovo svakih 5 minuta
# Save as simple-sync.ps1

Write-Host "Provjeravam ima li novih promjena..." -ForegroundColor Cyan

# 1. Povuci tude promjene
git pull origin main 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Preuzeo sam tude promjene!" -ForegroundColor Green
} else {
    Write-Host "Nema novih promjena ili greska" -ForegroundColor Yellow
}

# 2. Provjeri ima li mojih promjena
$status = git status --porcelain 2>$null

if ($status) {
    Write-Host "Imam promjene za poslati..." -ForegroundColor Yellow

    # Dodaj sve promjene
    git add . 2>$null

    # Spremi promjene sa porukom
    $vrijeme = Get-Date -Format "HH:mm"
    git commit -m "Promjene u $vrijeme" 2>$null

    # Posalji na internet
    git push origin main 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Poslao sam promjene! Prijatelj ce ih vidjeti." -ForegroundColor Green
    } else {
        Write-Host "Ne mogu poslati - netko drugi je promijenio prije mene" -ForegroundColor Red
    }
} else {
    Write-Host "Sve je vec sinhronizirano!" -ForegroundColor Gray
}

Write-Host "Gotovo! Mozes nastaviti raditi." -ForegroundColor Green