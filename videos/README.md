# Vidéos de démonstration

## 1) Fichiers déjà prêts (aucune action requise)
Trois screencasts du terminal sont déjà générés, en **GIF** (lecture inline sur
GitHub) et en **MP4** :

| Scène | Fichiers |
|-------|----------|
| Écoute non sécurisée | `demo1_sniffing.gif` / `.mp4` |
| Usurpation de capteur (Scapy) | `demo2_injection.gif` / `.mp4` |
| SROS2 chiffre et bloque | `demo3_sros2.gif` / `.mp4` |

Pour les régénérer : `powershell -ExecutionPolicy Bypass -File .\videos\make_videos.ps1`
(rendu des images via le conteneur, encodage MP4 via ffmpeg).

> ⚠️ Les scripts `demoN_*.ps1` ci-dessous **ne créent pas** de vidéo : ils
> *jouent* la démo dans le terminal. Pour en faire une vidéo, il faut
> **enregistrer l'écran avec OBS pendant** leur exécution (voir ci-dessous).

## 2) Enregistrer soi-même avec OBS (démo live, utile pour montrer Wireshark)

Chaque scène est un script « clé en main » : il affiche une narration à l'écran et
exécute les commandes tout seul — vous n'avez qu'à **lancer l'enregistrement OBS
puis le script**.

## Réglages OBS conseillés
- Source : **Capture d'écran** (ou Capture de fenêtre sur le terminal PowerShell).
- Sortie : MP4, 1080p, 30 fps.
- Agrandissez la police du terminal (Ctrl + molette) pour la lisibilité.

## Scènes

| Clip | Script | Durée | Montre |
|------|--------|-------|--------|
| 1. Écoute non sécurisée | `demo1_sniffing.ps1` | ~70 s | topics visibles, mesures en clair, texte lisible dans la capture |
| 2. Usurpation de capteur | `demo2_injection.ps1` | ~45 s | le subscriber bascule de `24.x` à la fausse valeur `99.9` |
| 3. SROS2 | `demo3_sros2.ps1` | ~90 s | trafic chiffré (0 texte), injection rejetée, écoute impossible |

Depuis la racine du dépôt :
```powershell
powershell -ExecutionPolicy Bypass -File .\videos\demo1_sniffing.ps1
powershell -ExecutionPolicy Bypass -File .\videos\demo2_injection.ps1
powershell -ExecutionPolicy Bypass -File .\videos\demo3_sros2.ps1
```

**Ordre** : jouez 1 → 2 → 3. Le clip 3 réactive SROS2 puis **restaure** le mode
non sécurisé à la fin. Pour un rendu optimal du clip 2, montrez en parallèle une
fenêtre `docker logs -f ros2_subscriber`.

## Bonus Wireshark (facultatif, à filmer à la main)
Pour une scène Wireshark : ouvrir `ros2_lab/captures/unsecured.pcap` (filtre
`rtps.sm.id == 0x15`, déplier un paquet → charge lisible), puis
`ros2_lab/captures/secured.pcap` (même manip → charge chiffrée).
