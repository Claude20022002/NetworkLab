#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_figures.py -- Genere les figures "donnees" du rapport (hex clair vs chiffre,
captures terminal). Utilise scapy + matplotlib. A lancer dans le conteneur ros2-lab.

Sorties dans figures/ :
  - fig_payload_comparaison.png : octets d'un paquet /sensor_data AVANT vs APRES SROS2
  - fig_subscriber_spoofe.png   : log du subscriber recevant la fausse valeur (A5)
  - fig_injection_bloquee.png   : injection rejetee sous SROS2 (B4)
  - fig_ecoute_bloquee.png      : ecoute pirate rejetee sous SROS2 (B4)
"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scapy.all import rdpcap, UDP, Raw

CAP = 'ros2_lab/captures'
FIG = 'figures'
os.makedirs(FIG, exist_ok=True)
MONO = font_manager.FontProperties(family='monospace', size=9)


def hexdump_lines(data, maxlen=160):
    data = data[:maxlen]
    out = []
    for off in range(0, len(data), 16):
        chunk = data[off:off + 16]
        hexpart = ' '.join('%02x' % b for b in chunk)
        hexpart = '%-47s' % hexpart
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        out.append(('%04x  %s  %s' % (off, hexpart, asc), asc))
    return out


def pick_plain(path):
    for p in rdpcap(path):
        if UDP in p and Raw in p and b'temperature' in bytes(p[Raw]):
            return bytes(p[UDP].payload)
    return b''


def pick_cipher(path):
    best = b''
    for p in rdpcap(path):
        if UDP in p and 7410 <= p[UDP].dport <= 7420 and Raw in p:
            raw = bytes(p[UDP].payload)
            if b'temperature' not in raw and len(raw) > len(best):
                best = raw
    if not best:  # repli : plus gros paquet du range
        for p in rdpcap(path):
            if UDP in p and Raw in p:
                raw = bytes(p[UDP].payload)
                if b'temperature' not in raw and len(raw) > len(best):
                    best = raw
    return best


def render_hex_panel(ax, title, subtitle, data, highlight_ascii=True, color='#145a32'):
    ax.axis('off')
    ax.text(0.0, 1.11, title, transform=ax.transAxes, fontsize=13,
            fontweight='bold', color=color)
    ax.text(0.0, 1.03, subtitle, transform=ax.transAxes, fontproperties=MONO,
            fontsize=8.5, color='#555')
    lines = hexdump_lines(data)
    y = 0.93
    for text, asc in lines:
        hot = highlight_ascii and ('temperature' in asc or 'pressure' in asc)
        ax.text(0.0, y, text, transform=ax.transAxes, fontproperties=MONO,
                color=('#c0392b' if hot else '#222'),
                bbox=dict(boxstyle='round,pad=0.1', fc='#fdecea', ec='none')
                if hot else None)
        y -= 0.060


def fig_comparaison():
    plain = pick_plain('%s/unsecured.pcap' % CAP) or pick_plain('%s/inject.pcap' % CAP)
    cipher = pick_cipher('%s/secured.pcap' % CAP)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2))
    render_hex_panel(a1, 'AVANT SROS2  —  lisible',
                     'unsecured.pcap · paquet DDS /sensor_data (charge en clair)',
                     plain, True, '#145a32')
    render_hex_panel(a2, 'APRES SROS2  —  chiffre',
                     'secured.pcap · meme topic, charge chiffree (AES-GCM)',
                     cipher, False, '#7b241c')
    fig.suptitle('Lecture de la charge utile DDS : avant / apres SROS2',
                 fontsize=13, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig('%s/fig_payload_comparaison.png' % FIG, dpi=140,
                bbox_inches='tight', facecolor='white')
    print('[+] fig_payload_comparaison.png')


def render_terminal(txtfile, outpng, title, highlight=None, bad=False):
    with open('%s/%s' % (CAP, txtfile), encoding='utf-8', errors='replace') as f:
        lines = [l.rstrip('\n') for l in f]
    h = max(2.2, 0.28 * len(lines) + 1.0)
    fig, ax = plt.subplots(figsize=(11, h))
    ax.set_facecolor('#1e1e1e'); fig.patch.set_facecolor('#1e1e1e')
    ax.axis('off')
    ax.text(0.01, 1.02, title, transform=ax.transAxes, fontproperties=MONO,
            fontsize=11, color='#ddd', fontweight='bold')
    y = 0.96
    for l in lines:
        col = '#8ae234'  # vert terminal
        if highlight and highlight in l:
            col = '#ff5c57'  # rouge = valeur usurpee / rejet
        if bad and ('X' in l[:6] or 'WARNING' in l or 'Could not' in l):
            col = '#ff5c57'
        ax.text(0.01, y, l, transform=ax.transAxes, fontproperties=MONO,
                fontsize=9, color=col)
        y -= 0.9 / max(len(lines), 1)
    fig.savefig(outpng, dpi=140, facecolor='#1e1e1e', bbox_inches='tight')
    print('[+]', outpng)


def main():
    fig_comparaison()
    render_terminal('subscriber_spoofed.txt', '%s/fig_subscriber_spoofe.png' % FIG,
                    'subscriber_node  —  injection Scapy (Partie A, etape 5)',
                    highlight='99.9')
    render_terminal('inject_blocked.txt', '%s/fig_injection_bloquee.png' % FIG,
                    'injection Scapy sous SROS2  —  REJETEE (Partie B, etape 4)', bad=True)
    render_terminal('eavesdrop_blocked.txt', '%s/fig_ecoute_bloquee.png' % FIG,
                    'ecoute pirate sous SROS2  —  REJETEE (Partie B, etape 4)', bad=True)


if __name__ == '__main__':
    main()
