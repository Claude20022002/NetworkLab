#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_videos.py -- Genere des screencasts "terminal" (GIF) des 3 demos du TP,
a partir des sorties reelles observees. A lancer dans le conteneur ros2-lab.
Les MP4 sont ensuite produits cote hote avec ffmpeg (voir make_videos.ps1).
Sorties : videos/demo1_sniffing.gif, demo2_injection.gif, demo3_sros2.gif
          + videos/_frames/demoN/*.png (pour l'encodage MP4)
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 980, 560
TITLE_H = 42
PAD = 18
LH = 23
BG = (30, 30, 30)
BAR = (45, 45, 48)
COL = {
    'narr': (52, 226, 226),   # cyan  : narration
    'cmd':  (138, 226, 52),   # vert  : commande
    'out':  (208, 208, 208),  # blanc : sortie
    'bad':  (255, 92, 87),    # rouge : fausse valeur / rejet
    'good': (115, 210, 22),   # vert vif : succes securite
}
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
f = ImageFont.truetype(FONT, 16)
fb = ImageFont.truetype(FONTB, 16)
ftitle = ImageFont.truetype(FONTB, 17)
VIS = (H - TITLE_H - 2 * PAD) // LH


def frame(title, lines):
    img = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, TITLE_H], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 15, 30 + i * 22, 29], fill=c)
    d.text((92, 12), title, font=ftitle, fill=(220, 220, 220))
    shown = lines[-VIS:]
    y = TITLE_H + PAD
    for text, style in shown:
        d.text((PAD, y), text, font=(fb if style in ('narr',) else f), fill=COL[style])
        y += LH
    return img


def build(name, title, events, out):
    """events: liste de (texte, style, hold_frames). Revelation ligne par ligne."""
    frames, lines = [], []
    for text, style, hold in events:
        lines.append((text, style))
        img = frame(title, lines)
        for _ in range(hold):
            frames.append(img.copy())
    for _ in range(14):           # tenue finale
        frames.append(frames[-1].copy())
    fdir = 'videos/_frames/%s' % name
    os.makedirs(fdir, exist_ok=True)
    for i, im in enumerate(frames):
        im.save('%s/%04d.png' % (fdir, i))
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=140, loop=0, optimize=True)
    print('[+] %s (%d frames)' % (out, len(frames)))


N, C, O, B, G = 'narr', 'cmd', 'out', 'bad', 'good'

demo1 = [
    ('>>> Deux noeuds ROS2 communiquent sur un reseau Docker isole, SANS securite.', N, 7),
    ('$ docker ps', C, 3),
    ('ros2_publisher    Up', O, 1), ('ros2_subscriber   Up', O, 1),
    ('ros2_attacker     Up', O, 3),
    ('>>> 1) L\'attaquant liste les topics (aucune authentification)', N, 6),
    ('$ ros2 topic list', C, 3),
    ('/commands', O, 1), ('/parameter_events', O, 1), ('/rosout', O, 1),
    ('/sensor_data', O, 3),
    ('>>> 2) Il lit les mesures du capteur EN CLAIR', N, 6),
    ('$ ros2 topic echo /sensor_data', C, 3),
    ("data: 'temperature: 24.5, pressure: 1013.2'", O, 2),
    ("data: 'temperature: 24.6, pressure: 1012.8'", O, 2),
    ("data: 'temperature: 24.4, pressure: 1013.5'", O, 2),
    ("data: 'temperature: 24.7, pressure: 1013.1'", O, 3),
    ('>>> 3) Capture reseau (12 s) + recherche de texte lisible', N, 6),
    ('$ tcpdump -i br-xxxx udp portrange 7400-7500', C, 3),
    ('197 packets captured', O, 2),
    ("Occurrences de 'temperature' en clair : 135", B, 6),
    ('>>> Sans SROS2 : topologie + donnees entierement exposees.', N, 8),
]

demo2 = [
    ('>>> Flux NORMAL recu par le subscriber (temperature ~24 C)', N, 6),
    ('[subscriber] sensor_data <- "temperature: 24.4, pressure: 1012.9"', O, 2),
    ('[subscriber] sensor_data <- "temperature: 24.6, pressure: 1013.5"', O, 2),
    ('[subscriber] sensor_data <- "temperature: 24.5, pressure: 1013.0"', O, 3),
    ('>>> L\'attaquant forge et injecte de FAUX paquets DDS (Scapy)', N, 6),
    ('$ python3 inject_dds.py --iface br-xxxx --count 8', C, 3),
    ('[*] Valeur reelle : temperature: 24.4, pressure: 1013.0', O, 2),
    ('    SN 129 -> 209 (accepte : numero de sequence superieur)', O, 2),
    ('[+] 8 paquets usurpes emis', O, 3),
    ('>>> Resultat : le subscriber affiche la FAUSSE valeur', N, 6),
    ('[subscriber] sensor_data <- "temperature: 99.9, pressure: 6666.6"', B, 2),
    ('[subscriber] sensor_data <- "temperature: 99.9, pressure: 6666.6"', B, 2),
    ('[subscriber] sensor_data <- "temperature: 99.9, pressure: 6666.6"', B, 2),
    ('[subscriber] sensor_data <- "temperature: 99.9, pressure: 6666.6"', B, 2),
    ('[subscriber] sensor_data <- "temperature: 99.9, pressure: 6666.6"', B, 3),
    ('>>> Spoofing reussi : fausse donnee = mauvaise decision = danger.', N, 8),
]

demo3 = [
    ('>>> Activation de SROS2 (X.509 + chiffrement AES-GCM + permissions)', G, 6),
    ('$ ROS_SECURITY_ENABLE=true docker compose up -d', C, 3),
    ('>>> Le subscriber authentifie recoit toujours', N, 4),
    ('[subscriber] sensor_data <- "temperature: 24.5, pressure: 1013.2"', O, 4),
    ('>>> 1) La charge est-elle encore lisible ?', N, 6),
    ('$ tcpdump ... | grep -c temperature', C, 3),
    ('158 packets captured', O, 2),
    ("Occurrences de 'temperature' en clair : 0   <- CHIFFRE", G, 6),
    ('>>> 2) Rejeu de l\'injection Scapy sous SROS2', N, 6),
    ('[X] Aucun paquet EN CLAIR a recopier : trame forgee rejetee', B, 5),
    ('>>> 3) Ecoute par un attaquant sans certificat', N, 6),
    ('WARNING: topic [/sensor_data] does not appear to be published', B, 2),
    ('Could not determine the type for the passed topic', B, 4),
    ('>>> Chiffrement OK, injection rejetee, ecoute impossible.', G, 8),
]

if __name__ == '__main__':
    os.makedirs('videos', exist_ok=True)
    build('demo1', 'Demo 1  -  Ecoute du trafic ROS2 non securise (Partie A)',
          demo1, 'videos/demo1_sniffing.gif')
    build('demo2', 'Demo 2  -  Usurpation d\'un capteur - Scapy (Partie A.5)',
          demo2, 'videos/demo2_injection.gif')
    build('demo3', 'Demo 3  -  SROS2 chiffre et bloque les attaques (Partie B)',
          demo3, 'videos/demo3_sros2.gif')
