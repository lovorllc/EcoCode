Param(
  [Parameter(Mandatory=$true)][string]$Package,
  [int]$Port = 8700
)

# Ensure adb is available
if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
  Write-Error "adb not found in PATH. Install Android platform-tools and ensure adb is on PATH."
  exit 1
}

# Wait up to N seconds for the package process to appear, polling every 2s
$timeoutSeconds = 60
$start = Get-Date
$pid = $null
while (((Get-Date) - $start).TotalSeconds -lt $timeoutSeconds) {
  # Try pidof (newer Android)
  try { $pid = (& adb shell pidof $Package) 2>$null } catch { $pid = $null }
  if ($pid -and $pid.Trim() -ne "") { break }
  # Fallback: parse ps output
  try { $ps = (& adb shell ps -A) 2>$null } catch { $ps = $null }
  if ($ps) {
    foreach ($line in $ps -split "`n") {
      if ($line -match $Package) {
        $cols = $line -split "\s+"
        if ($cols.Length -ge 2) { $pid = $cols[1]; break }
      }
    }
  }
  if ($pid -and $pid.Trim() -ne "") { break }
  Write-Host "Waiting for package '$Package' to appear (polling)..."
  Start-Sleep -Seconds 2
}

if (-not $pid -or $pid.Trim() -eq "") {
  Write-Warning "Could not find process for package '$Package' within $timeoutSeconds seconds. Attempting to start the app in debug mode and poll again..."
  # Try to start the app in debug mode (-D). Try common launcher activity names.
  $startCmds = @(
    "adb shell am start -D -n $Package/.LoginActivity",
    "adb shell am start -D -n $Package/.MainActivity",
    "adb shell monkey -p $Package -c android.intent.category.LAUNCHER 1"
  )
  foreach ($cmd in $startCmds) {
    Write-Host "Running: $cmd"
    try { iex $cmd } catch { }
    Start-Sleep -Seconds 2
  }
  # Poll again for another 30 seconds
  $timeoutSeconds2 = 30
  $start2 = Get-Date
  while (((Get-Date) - $start2).TotalSeconds -lt $timeoutSeconds2) {
    try { $pid = (& adb shell pidof $Package) 2>$null } catch { $pid = $null }
    if ($pid -and $pid.Trim() -ne "") { break }
    try { $ps = (& adb shell ps -A) 2>$null } catch { $ps = $null }
    if ($ps) {
      foreach ($line in $ps -split "`n") {
        if ($line -match $Package) {
          $cols = $line -split "\s+"
          if ($cols.Length -ge 2) { $pid = $cols[1]; break }
        }
      }
    }
    if ($pid -and $pid.Trim() -ne "") { break }
    Write-Host "Waiting for package '$Package' to start (polling after start attempt)..."
    Start-Sleep -Seconds 2
  }
  if (-not $pid -or $pid.Trim() -eq "") {
    Write-Error "Could not find process for package '$Package' after start attempts. Ensure the app is installed and built with debug enabled."
    exit 2
  }
}
$pid = $pid.Trim()
Write-Host "Found pid $pid for $Package. Forwarding jdwp:$pid to tcp:$Port ..."

& adb forward tcp:$Port jdwp:$pid
if ($LASTEXITCODE -eq 0) {
  Write-Host "Forwarded jdwp:$pid -> tcp:$Port"
  exit 0
} else {
  Write-Error "adb forward failed with exit code $LASTEXITCODE"
  exit $LASTEXITCODE
}