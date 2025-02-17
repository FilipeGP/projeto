# -*- coding: utf-8 -*-

from scapy.all import *
import time
import numpy as np
from multiprocessing import Process

def send_goose_packet_with_payload():
    pkt = Ether()
    pkt.src = "00:00:00:00:00:01"
    pkt.dst = "00:00:00:00:00:04"
    pkt.type = 0x88b8
    payload = "espaco reservado para o conteudo util de um pacote GOOSE - Generic Object Oriented Substation Event generico (O presente trabalho tem por objetivo testar a confiabilidade do protocolo IEC-61850, focando mais especificamente a transmissão de dados via mensagens GOOSE como substituta a ligação direta via cabo de entradas e saídas binárias das IED`s.Pretende-se realizar uma serie de testes para aferição dos tempos de reação de reles de proteção de barra no bloqueio seletivo de desligamento de alimentadores no advento de atuação devido a sobre corrente, utilizando duas montagens diferentes. Primeiramente utilizando-se a arquitetura clássica, ligação direta via cabo de entradas e saídas binárias e posteriormente através de uma conexão via rede IEC-61850, com a passagem de eventos via mensagens GOOSE e SV.)"
    pkt = pkt/Raw(load=payload)
    sendp(pkt, iface="h1-eth0", verbose=False)

def send_packets(rate):
    while True:
        send_goose_packet_with_payload()
        # Generate the next wait time from an exponential distribution
        wait_time = np.random.exponential(1.0 / rate)
        time.sleep(wait_time)

if __name__ == '__main__':
    rate = 40000  # average rate of packets per second
    processes = []
    for _ in range(70):  # Number of processes
        p = Process(target=send_packets, args=(rate,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
