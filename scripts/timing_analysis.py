#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timing_analysis.py  --  Fingerprinting par analyse temporelle (TP Partie B, etape 5)
====================================================================================

Meme lorsque la charge utile est CHIFFREE par SROS2, l'ESPACEMENT des paquets
(inter-packet timing) reste visible en clair sur le reseau. Ce script mesure la
distribution des intervalles inter-paquets pour deux scenarios et montre qu'on
peut distinguer l'etat du robot (en deplacement vs a l'arret) sans dechiffrer :
c'est une attaque par CANAL AUXILIAIRE (covert / side channel).

  - navigating.pcap : robot en deplacement -> paquets frequents et irreguliers
  - idle.pcap       : robot a l'arret      -> paquets rares et reguliers

Sortie : statistiques + histogramme compare -> figures/timing_plot.png
Usage  : python3 timing_analysis.py [navigating.pcap] [idle.pcap] [sortie.png]
"""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scapy.all import rdpcap, UDP


def inter_packet_ms(pcap_path):
    pkts = rdpcap(pcap_path)
    ts = [float(p.time) for p in pkts
          if UDP in p and 7400 <= p[UDP].dport <= 7500]
    ts.sort()
    if len(ts) < 2:
        return np.array([]), 0.0
    d = np.diff(np.array(ts)) * 1000.0  # millisecondes
    duration = ts[-1] - ts[0]
    rate = len(ts) / duration if duration > 0 else 0.0
    return d, rate


def describe(name, d, rate):
    if d.size == 0:
        print('  %-12s : aucun paquet' % name)
        return
    print('  %-12s : %5d paquets | %5.1f pq/s | intervalle moyen %7.1f ms '
          '| ecart-type %7.1f ms | median %7.1f ms'
          % (name, d.size + 1, rate, d.mean(), d.std(), np.median(d)))


def main():
    nav = sys.argv[1] if len(sys.argv) > 1 else 'ros2_lab/captures/navigating.pcap'
    idle = sys.argv[2] if len(sys.argv) > 2 else 'ros2_lab/captures/idle.pcap'
    out = sys.argv[3] if len(sys.argv) > 3 else 'figures/timing_plot.png'

    d_nav, r_nav = inter_packet_ms(nav)
    d_idle, r_idle = inter_packet_ms(idle)

    print('[*] Analyse temporelle (inter-packet timing) :')
    describe('navigating', d_nav, r_nav)
    describe('idle', d_idle, r_idle)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    bins = np.linspace(0, max(1200, np.percentile(d_idle, 95) if d_idle.size else 1200), 60)

    ax1.hist(d_nav, bins=bins, color='#c0392b', alpha=0.85)
    ax1.set_title('Robot en DEPLACEMENT (navigating)\n%.1f paquets/s' % r_nav)
    ax1.set_xlabel('Intervalle inter-paquets (ms)')
    ax1.set_ylabel('Nombre de paquets')
    ax1.axvline(d_nav.mean() if d_nav.size else 0, color='k', ls='--', lw=1,
                label='moyenne %.0f ms' % (d_nav.mean() if d_nav.size else 0))
    ax1.legend()

    ax2.hist(d_idle, bins=bins, color='#2980b9', alpha=0.85)
    ax2.set_title('Robot a l\'ARRET (idle)\n%.1f paquets/s' % r_idle)
    ax2.set_xlabel('Intervalle inter-paquets (ms)')
    ax2.set_ylabel('Nombre de paquets')
    ax2.axvline(d_idle.mean() if d_idle.size else 0, color='k', ls='--', lw=1,
                label='moyenne %.0f ms' % (d_idle.mean() if d_idle.size else 0))
    ax2.legend()

    fig.suptitle('Fingerprinting SROS2 : le timing trahit l\'etat du robot '
                 'malgre le chiffrement', fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=130)
    print('[+] Figure enregistree : %s' % out)


if __name__ == '__main__':
    main()
