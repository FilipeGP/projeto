import csv
import os
import logging as log
from collections import defaultdict
import numpy as np
import subprocess
import time

# Configurações iniciais
ALPHA = 0.2
GAMMA = 0.9
EPSILON = 0.3

# Largura de banda inicial para cada fila
largura_banda_atual_q0 = 8000000
largura_banda_atual_q1 = 8000000
largura_banda_atual_q2 = 4000000

# Definição das novas ações considerando ajustes em 100000 kbps
ACOES = [
    (800000, -800000, 0),  # Aumenta Q0 e diminui Q1, Q2 permanece
    (-800000, 800000, 0),  # Diminui Q0 e aumenta Q1, Q2 permanece
    (0, 0, 0),           # Mantém todas as filas
    (0, 800000, -800000),  # Aumenta Q1 e diminui Q2, Q0 permanece
    (0, -800000, 800000),  # Diminui Q1 e aumenta Q2, Q0 permanece
    (800000, 0, -800000),  # Aumenta Q0 e diminui Q2, Q1 permanece
    (-800000, 0, 800000),  # Diminui Q0 e aumenta Q2, Q1 permanece
]
ESPACO_ACOES = len(ACOES)

# Limites mínimos de largura de banda para cada fila
MIN_LARGURA_BANDA_Q0_KBPS = 800000
MIN_LARGURA_BANDA_Q1_KBPS = 800000
MIN_LARGURA_BANDA_Q2_KBPS = 800000

# Estrutura de valores Q ajustada para simplificar o acesso
valores_q = defaultdict(lambda: defaultdict(float))

# Prioridade das filas (0 tem maior prioridade)
PRIORIDADE_FILA = [0, 1, 2]

def criar_arquivo_csv():
    arquivo_existe = os.path.isfile('dados_largura_banda.csv')
    if not arquivo_existe:
        with open('dados_largura_banda.csv', mode='w', newline='') as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(['Episodio', 'Tempo', 'Largura_Banda_Q0', 'Largura_Banda_Q1', 'Largura_Banda_Q2', 'Recompensa_Q0', 'Recompensa_Q1', 'Recompensa_Q2', 'Ocupacao_Q0', 'Ocupacao_Q1', 'Ocupacao_Q2'])

criar_arquivo_csv()

def salvar_valores_q_para_csv():
    with open('dados_valores_q.csv', 'w', newline='') as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(['Estado', 'Indice_Acao', 'Valor_Q'])
        for estado, acoes in valores_q.items():
            for indice_acao, valor_q in acoes.items():
                escritor.writerow([estado, indice_acao, valor_q])

def carregar_valores_q_de_csv():
    if os.path.isfile('dados_valores_q.csv'):
        with open('dados_valores_q.csv', 'r', newline='') as arquivo:
            leitor = csv.reader(arquivo)
            next(leitor)  # Ignora a linha do cabeçalho
            for linha in leitor:
                estado = tuple(map(int, linha[0][1:-1].split(',')))
                indice_acao = int(linha[1])
                valores_q[estado][indice_acao] = float(linha[2])

criar_arquivo_csv()
carregar_valores_q_de_csv()

def escolher_acao_valida(estado, epsilon, ocupacoes):
    acoes_validas = []
    for i, acao in enumerate(ACOES):
        nova_largura_banda_q0 = largura_banda_atual_q0 + acao[0]
        nova_largura_banda_q1 = largura_banda_atual_q1 + acao[1]
        nova_largura_banda_q2 = largura_banda_atual_q2 + acao[2]
        if (nova_largura_banda_q0 >= MIN_LARGURA_BANDA_Q0_KBPS and
            nova_largura_banda_q1 >= MIN_LARGURA_BANDA_Q1_KBPS and
            nova_largura_banda_q2 >= MIN_LARGURA_BANDA_Q2_KBPS):
            acoes_validas.append(i)
    
    if np.random.uniform(0, 1) < epsilon:
        return np.random.choice(acoes_validas)
    else:
        if estado not in valores_q:
            valores_q[estado] = defaultdict(float)
        
        filas_cheias = [i for i, ocup in enumerate(ocupacoes) if ocup >= 85]
        if len(filas_cheias) > 1:
            fila_prioridade = min(filas_cheias, key=lambda x: PRIORIDADE_FILA[x])
            acoes_validas = [i for i in acoes_validas if ACOES[i][fila_prioridade] > 0]
        
        return max(acoes_validas, key=lambda a: valores_q[estado][a])

def obter_recompensa(taxa_ocupacao):
    """Obtém a recompensa."""
    if taxa_ocupacao > 99:
        return -50
    elif taxa_ocupacao > 94:
        return -40
    elif taxa_ocupacao > 90:
        return -30
    elif taxa_ocupacao > 85:
        return -20  
    elif taxa_ocupacao > 80:
        return -10  
    else:
        return 100

def aplicar_acao_para_largura_banda(largura_banda_atual_q0, largura_banda_atual_q1, largura_banda_atual_q2, acao):
    """Aplica a ação às larguras de banda atuais."""
    acao_q0, acao_q1, acao_q2 = acao

    nova_largura_banda_q0 = largura_banda_atual_q0 + acao_q0
    nova_largura_banda_q1 = largura_banda_atual_q1 + acao_q1
    nova_largura_banda_q2 = largura_banda_atual_q2 + acao_q2

    nova_largura_banda_q0 = max(MIN_LARGURA_BANDA_Q0_KBPS, nova_largura_banda_q0)
    nova_largura_banda_q1 = max(MIN_LARGURA_BANDA_Q1_KBPS, nova_largura_banda_q1)
    nova_largura_banda_q2 = max(MIN_LARGURA_BANDA_Q2_KBPS, nova_largura_banda_q2)

    log.debug(f"Ações: {acao}, Novas Larguras de Banda: Q0={nova_largura_banda_q0}, Q1={nova_largura_banda_q1}, Q2={nova_largura_banda_q2}")
    return int(nova_largura_banda_q0), int(nova_largura_banda_q1), int(nova_largura_banda_q2)

contador_atualizacoes = 0

def atualizar_largura_banda(taxa_ocupacao_q0, taxa_ocupacao_q1, taxa_ocupacao_q2):
    global valores_q, largura_banda_atual_q0, largura_banda_atual_q1, largura_banda_atual_q2, contador_atualizacoes

    estado_atual = (int(taxa_ocupacao_q0) // 20, int(taxa_ocupacao_q1) // 20, int(taxa_ocupacao_q2) // 20)
    ocupacoes = [taxa_ocupacao_q0, taxa_ocupacao_q1, taxa_ocupacao_q2]

    indice_acao = escolher_acao_valida(estado_atual, EPSILON, ocupacoes)
    acao = ACOES[indice_acao]

    nova_largura_banda_q0, nova_largura_banda_q1, nova_largura_banda_q2 = aplicar_acao_para_largura_banda(largura_banda_atual_q0, largura_banda_atual_q1, largura_banda_atual_q2, acao)

    largura_banda_atual_q0 = nova_largura_banda_q0
    largura_banda_atual_q1 = nova_largura_banda_q1
    largura_banda_atual_q2 = nova_largura_banda_q2

    comando = f"ovs-vsctl -- set Port s1-eth4 qos=@newqos -- --id=@newqos create QoS type=linux-htb other-config:max-rate=10000000000 queues=0=@q0,1=@q1,2=@q2 -- --id=@q0 create Queue other-config:min-rate={nova_largura_banda_q0} other-config:max-rate={nova_largura_banda_q0} -- --id=@q1 create Queue other-config:min-rate={nova_largura_banda_q1} other-config:max-rate={nova_largura_banda_q1} -- --id=@q2 create Queue other-config:min-rate={nova_largura_banda_q2} other-config:max-rate={nova_largura_banda_q2}"

    try:
        subprocess.check_output(comando, shell=True)
        log.info("Configuração de filas atualizada com sucesso")
    except subprocess.CalledProcessError as e:
        log.error(f"Erro ao executar comando: {e.output.decode()}")

    novo_estado = (int(taxa_ocupacao_q0) // 20, int(taxa_ocupacao_q1) // 20, int(taxa_ocupacao_q2) // 20)

    recompensa_q0 = obter_recompensa(taxa_ocupacao_q0)
    recompensa_q1 = obter_recompensa(taxa_ocupacao_q1)
    recompensa_q2 = obter_recompensa(taxa_ocupacao_q2)

    proximo_indice_acao = escolher_acao_valida(novo_estado, EPSILON, ocupacoes)

    valores_q[estado_atual][indice_acao] += ALPHA * (
        (recompensa_q0 + recompensa_q1 + recompensa_q2) + GAMMA * valores_q[novo_estado][proximo_indice_acao] - valores_q[estado_atual][indice_acao])

    log.info(f"Largura de banda atualizada: Q0={nova_largura_banda_q0}kbps, Q1={nova_largura_banda_q1}kbps, Q2={nova_largura_banda_q2}kbps")
    log.info(f"Soma das larguras de banda: {nova_largura_banda_q0 + nova_largura_banda_q1 + nova_largura_banda_q2} bps")

    contador_atualizacoes += 1

    salvar_valores_q_para_csv()

    return nova_largura_banda_q0, nova_largura_banda_q1, nova_largura_banda_q2, recompensa_q0, recompensa_q1, recompensa_q2

carregar_valores_q_de_csv()

