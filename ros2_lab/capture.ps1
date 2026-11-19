# Capture le trafic DDS/RTPS du reseau Docker ros2_lab dans captures\<Nom>.pcap
# Usage : .\capture.ps1 -Name unsecured -Seconds 60   (puis ouvrir le .pcap dans Wireshark)
#         .\capture.ps1 -Name discovery -Seconds 30 -Restart
#           -> redemarre publisher + subscriber pendant la capture pour enregistrer
#              la decouverte SPDP/SEDP (noms de topics, types de messages).
param([string]$Name = "capture", [int]$Seconds = 60, [switch]$Restart)
$id = (docker network inspect -f '{{.Id}}' ros2_lab).Substring(0, 12)
$dir = Join-Path $PSScriptRoot "captures"
$compose = Join-Path $PSScriptRoot "docker-compose.yml"
Write-Host "Capture sur br-$id pendant $Seconds s -> captures\$Name.pcap"

$cid = docker run -d --net=host --cap-add NET_ADMIN --cap-add NET_RAW -v "${dir}:/captures" ros2-lab:humble `
    timeout $Seconds tcpdump -i "br-$id" -nn -w "/captures/$Name.pcap" udp portrange 7400-7500

if ($Restart) {
    Start-Sleep -Seconds 3
    Write-Host "Redemarrage de publisher et subscriber (decouverte DDS)..."
    docker compose -f $compose restart publisher subscriber 2>&1 | Out-Null
}

docker wait $cid | Out-Null
docker logs $cid 2>&1 | Select-String "captured|dropped" | ForEach-Object { Write-Host $_ }
docker rm $cid | Out-Null
Write-Host "Termine : $dir\$Name.pcap"
