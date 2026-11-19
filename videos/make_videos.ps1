# make_videos.ps1 -- (Re)genere les screencasts des demos : GIF (Pillow) + MP4 (ffmpeg).
# Produit videos\demo1_sniffing.{gif,mp4}, demo2_injection.{...}, demo3_sros2.{...}
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# 1) Rendu des GIF + frames PNG dans le conteneur (Pillow + police DejaVu)
$win = (Get-Location).Path
docker run --rm -v "${win}:/work" -w /work ros2-lab:humble python3 -I scripts/make_videos.py

# 2) Encodage MP4 avec ffmpeg (Windows). Ajuste le chemin si besoin.
$ff = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ff) { $ff = "$env:APPDATA\Python\Python313\Scripts\ffmpeg.exe" }
foreach ($d in "demo1_sniffing","demo2_injection","demo3_sros2") {
  $name = $d.Split("_")[0]
  & $ff -y -framerate 7 -i "videos\_frames\$name\%04d.png" `
      -vf "scale=980:560:flags=lanczos,format=yuv420p" -movflags +faststart "videos\$d.mp4"
}
Remove-Item videos\_frames -Recurse -Force
Write-Host "OK : GIF + MP4 dans videos\" -ForegroundColor Green
