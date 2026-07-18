$root = "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app"
$files = @(
  (Join-Path $root "src\styles\globals.css"),
  (Join-Path $root "src\styles\generated.css")
)

$map = @{
  "surface-1"  = @("#111111", "#f5f7ef")
  "surface-2"  = @("#1A1A1A", "#edf1e5")
  "surface-3"  = @("#2A2A2A", "#e3e9d8")
  "border"     = @("#333333", "#d6ddca")
  "text"       = @("#FFFFFF", "#111111")
  "text-muted" = @("#D1D5DB", "#4B5563")
  "text-faint" = @("#9CA3AF", "#6B7280")
  "success"    = @("#22c55e", "#22c55e")
  "danger"     = @("#ef4444", "#ef4444")
  "warning"    = @("#FFD700", "#FFD700")
  "info"       = @("#2f9be0", "#2563eb")
  "accent"     = @("#e6a92e", "#e6a92e")
  "brand"      = @("#0ea5e9", "#0ea5e9")
  "background" = @("#0a0a0a", "#fbfcf8")
  "white"      = @("#f8fafc", "#f8fafc")
  "black"      = @("#0f172a", "#0f172a")
  "on-brand"   = @("#ffffff", "#111111")
}

function ToTriplet($hex) {
  $h = $hex -replace '#', ''
  if ($h.Length -eq 3) { $h = -join ($h.ToCharArray() | ForEach-Object { "$_$_" }) }
  $r = [Convert]::ToInt32($h.Substring(0, 2), 16)
  $g = [Convert]::ToInt32($h.Substring(2, 2), 16)
  $b = [Convert]::ToInt32($h.Substring(4, 2), 16)
  return "$r $g $b"
}

$darkTrips = @{}; $lightTrips = @{}
foreach ($n in $map.Keys) { $darkTrips[$n] = ToTriplet $map[$n][0]; $lightTrips[$n] = ToTriplet $map[$n][1] }

foreach ($f in $files) {
  $lines = Get-Content $f
  $out = @()
  $seenZozi = $false
  foreach ($line in $lines) {
    if ($line -match '--zozi-logo-') { $seenZozi = $true }
    $matched = $false
    foreach ($name in $map.Keys) {
      $pattern = '^\s*--color-' + $name + ':\s*#[0-9a-fA-F]{3,8};'
      if ($line -match $pattern) {
        $triplet = if ($seenZozi) { $lightTrips[$name] } else { $darkTrips[$name] }
        $out += $line
        $out += ("  --color-" + $name + "-rgb: " + $triplet + ";")
        $matched = $true
        break
      }
    }
    if (-not $matched) { $out += $line }
  }
  $tmp = $f + ".tmp_rvb"
  Set-Content -Path $tmp -Value $out
  Move-Item -Path $tmp -Destination $f -Force
  Write-Host "Updated $f"
}
