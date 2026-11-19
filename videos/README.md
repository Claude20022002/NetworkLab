# Vidéos de démonstration (OBS)

Trois courtes captures vidéo illustrent le TP. Chaque scène est un script
« clé en main » : il affiche une narration à l'écran et exécute les commandes
tout seul — vous n'avez qu'à **lancer l'enregistrement OBS puis le script**.

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
