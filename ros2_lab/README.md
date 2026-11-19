# TP ROS2 / SROS2 — environnement Docker (Windows)

ROS2 **Humble** tourne dans Docker (image `ros2-lab:humble`, basée sur `ros:humble-ros-base`)
avec SROS2, Scapy, tcpdump, numpy et matplotlib. Wireshark est installé côté Windows.

| Conteneur         | Rôle                                                      |
|-------------------|-----------------------------------------------------------|
| `ros2_publisher`  | `publisher_node` : publie `/sensor_data` (10 Hz) et `/commands` (2 Hz) |
| `ros2_subscriber` | `subscriber_node` : affiche ce qu'il reçoit               |
| `ros2_attacker`   | poste attaquant (Scapy, ros2 CLI), dossier du TP monté dans `/lab/work` |

## Démarrer (Partie A, étape 1)
```powershell
docker network create --driver bridge ros2_lab   # déjà fait, ignorer l'erreur "already exists"
docker compose up -d
docker ps
docker exec -it ros2_attacker bash               # puis : ros2 topic list
docker logs -f ros2_subscriber                   # voir les messages reçus
```

## Capturer pour Wireshark (étapes A2 et B3)
Wireshark sous Windows ne voit pas le bridge Docker (il vit dans la VM de Docker Desktop).
Capturer avec le script, puis ouvrir le fichier dans Wireshark :
```powershell
.\capture.ps1 -Name unsecured -Seconds 60    # -> captures\unsecured.pcap
```
Dans Wireshark, utiliser le filtre d'affichage **`rtps`** : le port 7400 ne porte que la découverte
multicast, les données passent sur 7410+ (unicast).

## Scapy (étape A5)
Mettre `inject_dds.py` dans ce dossier puis :
`docker exec -it ros2_attacker python3 /lab/work/inject_dds.py`

## Partie B — SROS2 (corrections pour Humble)
Deux commandes de l'énoncé ne fonctionnent pas telles quelles sous Humble :
- le nom d'enclave doit commencer par `/` : `create_enclave keystore /publisher_node`
- la variable est **`ROS_SECURITY_ENABLE`** (sans D) et **`ROS_SECURITY_KEYSTORE`** (pas `_PATH`)

```powershell
docker exec -it ros2_attacker bash
  cd /lab/work
  ros2 security create_keystore keystore
  ros2 security create_enclave keystore /publisher_node
  ros2 security create_enclave keystore /subscriber_node
  exit
$env:ROS_SECURITY_ENABLE = "true"
docker compose up -d --force-recreate publisher subscriber
.\capture.ps1 -Name secured -Seconds 60
```
Le compose monte `./keystore` dans les nœuds et les lance avec `--enclave /publisher_node`
et `--enclave /subscriber_node`. Pour revenir au mode non sécurisé :
`Remove-Item Env:ROS_SECURITY_ENABLE; docker compose up -d --force-recreate publisher subscriber`

## Arrêter
`docker compose down`
