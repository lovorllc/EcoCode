Param(
  [int]$TimeoutSeconds = 30
)
$log = "${PSScriptRoot.replace('\','/')}/forward_jdwp.log"
function Log($msg){ $ts = Get-Date -Format o; "$ts - $msg" | Out-File -FilePath $log -Append }
Log "check_adb_device: starting (timeout ${TimeoutSeconds}s)"
if (-not (Get-Command adb -ErrorAction SilentlyContinue)){
  Log "ERROR: adb not found in PATH"
  Write-Error "adb not found in PATH. Install Android platform-tools and ensure adb is on PATH."
  exit 1
}
$start = Get-Date
while (((Get-Date)-$start).TotalSeconds -lt $TimeoutSeconds){
  try{
    $out = (& adb devices) 2>$null
  } catch { $out = "" }
  Log "adb devices output:\n$out"
  # find a non-empty device line other than the header
  $lines = $out -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
  $deviceLines = $lines | Where-Object { $_ -notmatch "List of devices" }
  if ($deviceLines.Count -gt 0){
    foreach ($l in $deviceLines){
      if ($l -match "device$" -or $l -match "unauthorized$" -or $l -match "online$"){
        Log "Device detected: $l"
        Write-Host "Device detected: $l"
        exit 0
      }
    }
  }
  Write-Host "Waiting for adb device..."
  Start-Sleep -Seconds 2
}
Log "ERROR: No adb devices found after ${TimeoutSeconds}s"
Write-Error "No adb devices found after ${TimeoutSeconds}s. Start an emulator or connect a device and ensure adb is in PATH."
exit 2