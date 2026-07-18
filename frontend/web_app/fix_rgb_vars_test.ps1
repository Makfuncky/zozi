$root = "D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app"
$files = @( Join-Path $root "globals_test.css" )
$map = @{
  "surface-1"  = @("#111111", "#f5f7ef")
  "danger"     = @("#ef4444", "#ef4444")
  "text"       = @("#FFFFFF", "#111111")
  "border"     = @("#333333", "#d6ddca")
}
function ToTriplet($hex) {
  $h = $hex -replace '#', ''
  if ($h.Length -eq 3) { $h = -join ($h.ToCharArray() | ForEach-Object { "$_$_" }) }
  return "$([Convert]::ToInt32($h.Substring(0,2),16)) $([Convert]::ToInt32($h.Substring(2,2),16)) $([Convert]::ToInt32($h.Substring(4,2),16))"
}
foreach ($f in $files) {
  $lines = Get-Content $f; $out = @(); $mode = "dark"
  foreach ($line in $lines) {
    if ($line -match '^\s*:root\s*\{') { $mode="dark"; $out+=$line; continue }
    if ($line -match '^\s*\.dark\s*\{') { $mode="dark"; $out+=$line; continue }
    if ($line -match '^\s*\.light\s*\{') { $mode="light"; $out+=$line; continue }
    if ($line -match '^\s*--color-[a-z0-9-]+-rgb:\s*[0-9 ]+;') { continue }
    $matched=$false
    foreach ($name in $map.Keys) {
      $pattern = '^\s*--color-' + $name + ':\s*#[0-9a-fA-F]{3,8};'
      if ($line -match $pattern) {
        $hex = if ($mode -eq 'dark') { $map[$name][0] } else { $map[$name][1] }
        $out += $line; $out += ("  --color-" + $name + "-rgb: " + (ToTriplet $hex) + ";"); $matched=$true; break
      }
    }
    if (-not $matched) { $out += $line }
  }
  Set-Content -Path $f -Value $out
  Write-Host "Rewrote $f"
}
Write-Host "=== danger + surface-1 rgb placement ==="
Select-String -Path $f -Pattern 'color-(danger|surface-1|text|border)-rgb:' | ForEach-Object { $_.LineNumber.ToString()+': '+$_.Line.Trim() }
