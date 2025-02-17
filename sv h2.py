# -*- coding: utf-8 -*-

from scapy.all import *
import time
from multiprocessing import Process

def send_custom_ethertype_packet_with_payload():
    pkt = Ether()
    pkt.src = "00:00:00:00:00:02"  
    pkt.dst = "00:00:00:00:00:04"  
    pkt.type = 0x88bA
    payload = "espaco reservado para o conteudo util de um pacote Sampled Values generico (O presente trabalho tem por objetivo testar a confiabilidade do protocolo IEC-61850, focando mais especificamente a transmissão de dados via mensagens GOOSE como substituta a ligação direta via cabo de entradas e saídas binárias das IED`s.Pretende-se realizar uma serie de testes para aferição dos tempos de reação de reles de proteção de barra no bloqueio seletivo de desligamento de alimentadores no advento de atuação devido a sobre corrente, utilizando duas montagens diferentes. Primeiramente utilizando-se a arquitetura clássica, ligação direta via cabo de entradas e saídas binárias e posteriormente através de uma conexão via rede IEC-61850, com a passagem de eventos via mensagens GOOSE e SV.) "
    pkt = pkt/Raw(load=payload)
    sendp(pkt, iface="h2-eth0", verbose=False)


def send_packets():
    while True:
        send_custom_ethertype_packet_with_payload()
        time.sleep(0.000000000002)  # Adjust the sleep time if necessary

if __name__ == '__main__':
    for _ in range(55):  # Number of processes
        p = Process(target=send_packets)
        p.start()
