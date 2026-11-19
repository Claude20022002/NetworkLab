# demo3_sros2.ps1 -- Scene video 3 : SROS2 chiffre et bloque les attaques (Partie B)
# Prerequis : keystore deja genere (ros2_lab/keystore). Duree ~90 s.
# A la fin, le lab est REMIS en mode non securise (etat par defaut).
$ErrorActionPreference = 'SilentlyContinue'
function Narr($t){ Write-Host "`n>>> $t`n" -ForegroundColor Green; Start-Sleep 2 }
Set-Location "$PSScriptRoot\..\ros2_lab"
$BR = "br-" + (docker network inspect -f '{{.Id}}' ros2_lab).Substring(0,12)
$cap = (Resolve-Path ".\captures").Path
$scripts = (Resolve-Path "..\scripts").Path

Narr "Activation de SROS2 (certificats X.509 + chiffrement AES-GCM + permissions) :"
docker compose stop publisher subscriber | Out-Null
$env:ROS_SECURITY_ENABLE="true"; $env:PUBLISH_COMMANDS="false"; $env:SUBSCRIBE_COMMANDS="false"
docker compose up -d --force-recreate publisher subscriber | Out-Null
Start-Sleep 11
Write-Host "Le subscriber (authentifie) recoit toujours :" -ForegroundColor Gray
docker logs --tail 2 ros2_subscriber | Select-String sensor_data

Narr "1) Capture reseau : la charge est-elle encore lisible ?"
docker run --rm --net=host --cap-add NET_ADMIN -v "${cap}:/captures" ros2-lab:humble `
  bash -c "timeout 10 tcpdump -i $BR -nn -w /captures/_demo.pcap udp portrange 7400-7500 2>&1 | grep captured; echo -n 'Occurrences de ''temperature'' en clair : '; tcpdump -r /captures/_demo.pcap -A 2>/dev/null | grep -c temperature"
docker run --rm -v "${cap}:/captures" ros2-lab:humble rm -f /captures/_demo.pcap | Out-Null

Narr "2) Rejeu de l'injection Scapy sous SROS2 :"
docker run --rm --net=host --cap-add NET_ADMIN --cap-add NET_RAW -v "${scripts}:/s" ros2-lab:humble `
  python3 -I /s/inject_dds.py --iface $BR --count 6 --timeout 10

Narr "3) Ecoute par un attaquant sans certificat :"
docker exec ros2_attacker bash -c "source /opt/ros/humble/setup.bash; ros2 daemon stop >/dev/null 2>&1; timeout 8 ros2 topic echo --once /sensor_data 2>&1 | head -3"

Narr "Chiffrement OK, injection rejetee, ecoute impossible. Retour en mode non securise."
docker compose stop publisher subscriber | Out-Null
Remove-Item Env:ROS_SECURITY_ENABLE, Env:PUBLISH_COMMANDS, Env:SUBSCRIBE_COMMANDS
docker compose up -d --force-recreate publisher subscriber | Out-Null
Write-Host "Lab restaure (non securise)." -ForegroundColor Gray
