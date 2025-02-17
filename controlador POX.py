from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpidToStr
import os
import subprocess
import logging
from pox.lib.recoco import Timer
from bandwidth_manager import atualizar_largura_banda # Certifique-se de que esta função retorna os valores corretos
from pox.openflow.of_json import flow_stats_to_list
import csv
from datetime import datetime

logging.basicConfig(
    filename='/home/app.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s',
    force=True
)

logging.getLogger().addHandler(logging.StreamHandler())

log = core.getLogger()

# Variáveis globais para armazenar as taxas de ocupação das filas
taxa_ocupacao_q0 = 0
taxa_ocupacao_q1 = 0
taxa_ocupacao_q2 = 0
perda_pacotes_q0 = 0
perda_pacotes_q1 = 0
perda_pacotes_q2 = 0

id_s1 = 0
id_s2 = 0

def criar_arquivo_csv():
    arquivo_existe = os.path.isfile('dados_ocupacao.csv')
    if not arquivo_existe:
        with open('dados_ocupacao.csv', mode='w', newline='') as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(['Hora', 'Ocupacao_Q0', 'Ocupacao_Q1', 'Ocupacao_Q2', 'PerdaPacotes_Q0', 'PerdaPacotes_Q1', 'PerdaPacotes_Q2', 'LarguraBanda_Q0', 'LarguraBanda_Q1', 'LarguraBanda_Q2', 'Recompensa_Q0', 'Recompensa_Q1', 'Recompensa_Q2'])

criar_arquivo_csv()

def _handle_ConnectionUp(event):
    global id_s1, id_s2
    print("Conexão estabelecida:", dpidToStr(event.connection.dpid))

    def definir_largura_banda(q0_bw, q1_bw, q2_bw):
        q0_bw = 8000000
        q1_bw = 8000000
        q2_bw = 4000000
        return (q0_bw, q1_bw, q2_bw)

    # Define o comando a ser executado
    (q0_bw, q1_bw, q2_bw) = definir_largura_banda(0, 0, 0)
    comando = f"ovs-vsctl -- set Port s1-eth4 qos=@newqos -- --id=@newqos create QoS type=linux-htb other-config:max-rate=100000000 queues=0=@q0,1=@q1,2=@q2 -- --id=@q0 create Queue other-config:min-rate={q0_bw} other-config:max-rate={q0_bw} -- --id=@q1 create Queue other-config:min-rate={q1_bw} other-config:max-rate={q1_bw} -- --id=@q2 create Queue other-config:min-rate={q2_bw} other-config:max-rate={q2_bw}"
    os.system(comando)

    # Armazena o dpid da conexão para o switch
    for porta in event.connection.features.ports:
        if porta.name == "s1-eth1":
            id_s1 = event.connection.dpid
            print("id_s1=", id_s1)
        elif porta.name == "s2-eth1":
            id_s2 = event.connection.dpid
            print("id_s2=", id_s2)

def _handle_PacketIn(event):
    global id_s1, id_s2

    if event.connection.dpid == id_s1:
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0806
        msg.actions.append(of.ofp_action_output(port=of.OFPP_ALL))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 100
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x88b8
        msg.match.nw_src = "10.0.0.1"
        msg.match.nw_dst = "10.0.0.4"
        msg.actions.append(of.ofp_action_enqueue(port=4, queue_id=0))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 100
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x88ba
        msg.match.nw_src = "10.0.0.2"
        msg.match.nw_dst = "10.0.0.4"
        msg.actions.append(of.ofp_action_enqueue(port=4, queue_id=1))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 100
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0800
        msg.match.nw_src = "10.0.0.3"
        msg.match.nw_dst = "10.0.0.4"
        msg.actions.append(of.ofp_action_enqueue(port=4, queue_id=2))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 10
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = "10.0.0.1"
        msg.actions.append(of.ofp_action_output(port=1))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 10
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = "10.0.0.2"
        msg.actions.append(of.ofp_action_output(port=2))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 10
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = "10.0.0.3"
        msg.actions.append(of.ofp_action_output(port=3))
        event.connection.send(msg)
    
        msg = of.ofp_flow_mod()
        msg.priority = 10
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.dl_type = 0x0800
        msg.match.nw_dst = "10.0.0.4"
        msg.actions.append(of.ofp_action_output(port=4))
        event.connection.send(msg)
    
    elif event.connection.dpid == id_s2:
        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.in_port = 1
        msg.actions.append(of.ofp_action_output(port=2))
        event.connection.send(msg)

        msg = of.ofp_flow_mod()
        msg.priority = 1
        msg.idle_timeout = 0
        msg.hard_timeout = 0
        msg.match.in_port = 2
        msg.actions.append(of.ofp_action_output(port=1))
        event.connection.send(msg)

def _request_queue_stats():
    for connection in core.openflow._connections.values():
        connection.send(of.ofp_stats_request(body=of.ofp_queue_stats_request()))
        log.info("Solicitação de estatísticas de fila enviada para %i conexão(ões)", len(core.openflow._connections))

def _handle_queue_stats(event):
    stats = flow_stats_to_list(event.stats)
    log.info("Estatísticas de Fila Recebidas de %s: %s", dpidToStr(event.connection.dpid), stats)

def obter_tamanho_fila(classe_fila):
    taxa_ocupacao_padrao = 0
    try:
        resultado = subprocess.check_output(['tc', '-s', 'class', 'show', 'dev', 's1-eth4', 'classid', classe_fila], stderr=subprocess.STDOUT)
        resultado_str = resultado.decode('utf-8')
        log.debug(f"Resultado do comando tc para {classe_fila}: {resultado_str}")
        tamanho_fila_bytes = None

        for linha in resultado_str.split("\n"):
            if "backlog" in linha:
                dados_backlog = linha.split()
                for palavra in dados_backlog:
                    if palavra.endswith('b'):
                        numero_str = palavra[:-1]
                        tamanho_fila_bytes = int(numero_str) if 'k' not in numero_str.lower() else int(numero_str[:-1]) * 1000
                        break

        if tamanho_fila_bytes is not None:
            max_length_bytes = 19640
            taxa_ocupacao = (tamanho_fila_bytes / max_length_bytes) * 100
            log.info(f"Taxa de ocupação para {classe_fila}: {taxa_ocupacao:.2f}%")
            return taxa_ocupacao
    except subprocess.CalledProcessError as e:
        log.error(f"Erro ao executar o comando tc: {e.output.decode()}")
    except Exception as e:
        log.error(f"Erro inesperado: {e}")

    return taxa_ocupacao_padrao

def obter_perda_pacotes(classe_fila):
    try:
        resultado = subprocess.check_output(['tc', '-s', 'class', 'show', 'dev', 's1-eth4', 'classid', classe_fila], stderr=subprocess.STDOUT)
        resultado_str = resultado.decode('utf-8')
        log.debug(f"Resultado do comando tc para {classe_fila}: {resultado_str}")

        perda_pacotes = 0

        for linha in resultado_str.split("\n"):
            if "dropped" in linha:
                dados_dropped = linha.split()
                for palavra in dados_dropped:
                    if palavra.endswith(','):
                        perda_pacotes = int(palavra[:-1])
                        break

        log.info(f"Perda de pacotes para {classe_fila}: {perda_pacotes} pacotes")
        return perda_pacotes
    except subprocess.CalledProcessError as e:
        log.error(f"Erro ao executar o comando tc: {e.output.decode()}")
    except Exception as e:
        log.error(f"Erro inesperado: {e}")

    return 0

def monitorar_filas():
    global taxa_ocupacao_q0, taxa_ocupacao_q1, taxa_ocupacao_q2
    global perda_pacotes_q0, perda_pacotes_q1, perda_pacotes_q2

    # Monitora a ocupação das filas e pacotes perdidos
    taxa_ocupacao_q0 = obter_tamanho_fila('1:1')
    taxa_ocupacao_q1 = obter_tamanho_fila('1:2')
    taxa_ocupacao_q2 = obter_tamanho_fila('1:3')
    perda_pacotes_q0 = obter_perda_pacotes('1:1')
    perda_pacotes_q1 = obter_perda_pacotes('1:2')
    perda_pacotes_q2 = obter_perda_pacotes('1:3')

    log.info(f"Taxas de Ocupação: q0={taxa_ocupacao_q0}%, q1={taxa_ocupacao_q1}%, q2={taxa_ocupacao_q2}%")
    log.info(f"Perda de Pacotes: q0={perda_pacotes_q0}, q1={perda_pacotes_q1}, q2={perda_pacotes_q2}")

    # Adiciona registro de tempo
    hora_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
   
    # Inicializa variáveis de largura de banda e recompensas
    nova_bw_q0, nova_bw_q1, nova_bw_q2, recompensa_q0, recompensa_q1, recompensa_q2 = 0, 0, 0, 0, 0, 0

    # Atualiza a largura de banda e calcula as recompensas somente se a ocupação das filas ultrapassar 80%
    if taxa_ocupacao_q0 > 80 or taxa_ocupacao_q1 > 80 or taxa_ocupacao_q2 > 80:
        nova_bw_q0, nova_bw_q1, nova_bw_q2, recompensa_q0, recompensa_q1, recompensa_q2 = atualizar_largura_banda(taxa_ocupacao_q0, taxa_ocupacao_q1, taxa_ocupacao_q2)

    # Escreve os dados no arquivo CSV
    with open('dados_ocupacao.csv', mode='a', newline='') as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow([hora_atual, taxa_ocupacao_q0, taxa_ocupacao_q1, taxa_ocupacao_q2, perda_pacotes_q0, perda_pacotes_q1, perda_pacotes_q2, nova_bw_q0, nova_bw_q1, nova_bw_q2, recompensa_q0, recompensa_q1, recompensa_q2])

def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    core.openflow.addListenerByName("QueueStatsReceived", _handle_queue_stats)
    Timer(0.1, monitorar_filas, recurring=True)

if __name__ == "__main__":
    launch()

