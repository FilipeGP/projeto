# -*- coding: utf-8 -*-

from scapy.all import *
import time
import numpy as np
from multiprocessing import Process
import binascii

def send_mms_packet_with_payload():
    # Construir o cabeçalho Ethernet
    pkt = Ether()
    pkt.src = "00:00:00:00:00:03"
    pkt.dst = "00:00:00:00:00:04"
    pkt.type = 0x0800  # EtherType para IP

    # Construir o cabeçalho IP
    ip = IP()
    ip.src = "10.0.0.3"
    ip.dst = "10.0.0.4"

    # Construir o cabeçalho TCP
    tcp = TCP()
    tcp.sport = 102  # Porta padrão para MMS
    tcp.dport = 102  # Porta padrão para MMS

    # Construir uma carga útil genérica
    generic_payload = "espaco reservado para o conteudo util de um pacote Sampled Values generico (O presente trabalho tem por objetivo testar a confiabilidade do protocolo IEC-61850, focando mais especificamente a transmissão de dados via mensagens GOOSE como substituta a ligação direta via cabo de entradas e saídas binárias das IED`s.Pretende-se realizar uma serie de testes para aferição dos tempos de reação de reles de proteção de barra no bloqueio seletivo de desligamento de alimentadores no advento de atuação devido a sobre corrente, utilizando duas montagens diferentes. Primeiramente utilizando-se a arquitetura clássica, ligação direta via cabo de entradas e saídas binárias e posteriormente através de uma conexão via rede IEC-61850, com a passagem de eventos via mensagens GOOSE e SV.) "

    # Construir o pacote final
    pkt = pkt/ip/tcp/Raw(load=generic_payload)
    
    # Enviar o pacote
    sendp(pkt, iface="h3-eth0", verbose=False)

def send_packets(rate):
    while True:
        send_mms_packet_with_payload()
        # Gerar o próximo tempo de espera a partir de uma distribuição exponencial
        wait_time = np.random.exponential(1.0 / rate)
        time.sleep(wait_time)

if __name__ == '__main__':
    rate = 5000000 # taxa média de pacotes por segundo
    processes = []
    for _ in range(50):  # Número de processos
        p = Process(target=send_packets, args=(rate,))
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
