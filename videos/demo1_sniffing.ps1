# demo1_sniffing.ps1 -- Scene video 1 : ecoute du trafic NON securise (Partie A)
# Lancez OBS (Enregistrer), puis ce script. Duree ~70 s.
$ErrorActionPreference = 'SilentlyContinue'
function Narr($t){ Write-Host "`n>>> $t`n" -ForegroundColor Cyan; Start-Sleep 2 }
Set-Location "$PSScriptRoot\..\ros2_lab"

Narr "Deux noeuds ROS2 communiquent sur le reseau Docker isole, SANS securite."
docker ps --filter name=ros2_ --format "{{.Names}} : {{.Status}}"
Start-Sleep 2

Narr "1) Un attaquant liste les topics sans aucune authentification :"
docker exec ros2_attacker bash -c "source /opt/ros/humble/setup.bash && ros2 topic list"
Start-Sleep 3

Narr "2) Il lit directement les mesures du capteur, EN CLAIR :"
docker exec ros2_attacker bash -c "source /opt/ros/humble/setup.bash && timeout 6 ros2 topic echo /sensor_data"
Start-Sleep 2

Narr "3) Capture reseau de 12 s sur le bridge Docker, puis recherche de texte lisible :"
$BR = "br-" + (docker network inspect -f '{{.Id}}' ros2_lab).Substring(0,12)
$cap = (Resolve-Path ".\captures").Path
docker run --rm --net=host --cap-add NET_ADMIN -v "${cap}:/captures" ros2-lab:humble `
  bash -c "timeout 12 tcpdump -i $BR -nn -w /captures/_demo.pcap udp portrange 7400-7500 2>&1 | grep captured; echo -n 'Occurrences de ''temperature'' en clair : '; tcpdump -r /captures/_demo.pcap -A 2>/dev/null | grep -c temperature"
Remove-Item .\captures\_demo.pcap -Force
Narr "Conclusion : sans SROS2, topologie + donnees sont entierement exposees."
