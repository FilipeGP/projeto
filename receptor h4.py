# -*- coding: utf-8 -*-
from scapy.all import *

def print_packet(packet):
    print(packet.summary())

sniff(iface="h4-eth0", prn=print_packet)
