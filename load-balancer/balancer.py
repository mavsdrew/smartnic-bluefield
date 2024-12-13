#!/usr/bin/env python3

from flask import Flask, request, jsonify
from collections import defaultdict
import os
import time
import random
import logging

# Configura o logging para rastrear operações do balanceador
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações dos servidores NGINX (obtidas de variáveis de ambiente ou valores padrão)
#SERVERS = ["192.168.1.101", "192.168.1.102", "192.168.1.103"]  # Servidores NGINX
#PORT = 80  # Porta padrão para HTTP
#strategy = "round_robin"  # Estratégia de balanceamento: round_robin ou least_connectionsn
SERVERS = os.getenv("SERVERS", "192.168.1.101,192.168.1.102,192.168.1.103").split(",")
PORT = int(os.getenv("PORT", 80))  # Porta padrão para HTTP
STRATEGY = os.getenv("STRATEGY", "round_robin")  # Estratégia de balanceamento: round_robin ou least_connections

# Estado compartilhado
current_server = 0  # Índice do servidor atual (para round_robin)
connections = defaultdict(int)  # Contador de conexões ativas para cada servidor (least_connections)
metrics = defaultdict(lambda: {"requests": 0, "latency": []})  # Métricas para cada servidor

# Endpoint principal para balanceamento
@app.route('/balance', methods=['POST'])
def balance():
    """
    Recebe requisições HTTP e distribui o fluxo para um dos servidores NGINX
    """
    global current_server  # Necessário para alterar o estado global do índice do servidor

    # Valida a entrada para garantir que 'flow_id' esteja presente
    if not request.json or "flow_id" not in request.json:
        return jsonify({"error": "Invalid request. Missing 'flow_id'"}), 400
    
    # Captura o fluxo ID da requisição ou gera um ID aleatório
    flow_id = request.json.get('flow_id', random.randint(1, 100000))
    start_time = time.time()  # Marca o tempo inicial para cálculo da latência
    # print(f"Processing flow: {flow_id}")  # Print simples para debug
    logging.info(f"Processing flow {flow_id}.")  # Log simples para debug

    # Escolhe o servidor baseado na estratégia configurada
    if STRATEGY == "round_robin":
        server = SERVERS[current_server]  # Escolhe o servidor atual
        current_server = (current_server + 1) % len(SERVERS)  # Avança para o próximo servidor
    elif STRATEGY == "least_connections":
        server = min(SERVERS, key=lambda s: connections[s])  # Servidor com menos conexões
        connections[server] += 1  # Incrementa o número de conexões para este servidor
    else:
        return jsonify({"erro": "Estratégia inválida"}), 400  # Retorna erro se a estratégia não for válida

    # Atualiza as métricas de desempenho/performance
    metrics[server]["requests"] += 1
    metrics[server]["latency"].append(time.time() - start_time)

    # Log da decisão de balanceamento
    logging.info(f"Flow {flow_id} directed to server {server} using {STRATEGY} strategy.")

    # Retorna a decisão do balanceamento (servidor e porta)
    return jsonify({"server": server, "porta": PORT, "flow_id": flow_id})

# Endpoint para liberar conexões após término do uso
@app.route('/release', methods=['POST'])
def release_flow():
    """
    Libera uma conexão do servidor especificado na requisição
    """
    # Obtém o servidor a partir do payload
    server = request.json.get('server')  # IP do servidor que está liberando uma conexão
    
    # Valida se o servidor fornecido existe na configuração
    if server not in SERVERS:
        return jsonify({"error": f"Server {server} is not in the server list."}), 400

    # Decrementa o contador de conexões do servidor, se aplicável
    if server in connections and connections[server] > 0:
        connections[server] -= 1  # Decrementa o contador de conexões

    # Log do evento de liberação
    logging.info(f"Connection released from server {server}.")

    return jsonify({"status": "ok"}), 200  # Retorna confirmação

# Endpoint de monitoramento
@app.route('/monitor', methods=['GET'])
def monitor():
    """
    Retorna métricas em tempo real para cada servidor:
    - Número de conexões ativas por servidor
    - Número total de requisições por servidor
    - Latência média, máxima e mínima
    """
    monitor_data = {}
    
    # Calcula métricas para cada servidor
    for server, data in metrics.items():
        total_requests = data["requests"]
        latencies = data["latency"]
        avg_latency = sum(latencies) / total_requests if total_requests > 0 else 0
        max_latency = max(latencies) if latencies else 0
        min_latency = min(latencies) if latencies else 0

        monitor_data[server] = {
            "active_connections": connections[server],  # Conexões ativas no momento
            "total_requests": total_requests,  # Total de requisições processadas
            "average_latency": avg_latency,  # Latência média das requisições
            "max_latency": max_latency,  # Latência máxima
            "min_latency": min_latency,  # Latência mínima
        }

    # Log do evento de monitoramento
    logging.info("Monitor data retrieved.")

    return jsonify(monitor_data)

if __name__ == "__main__":
    # Inicia a aplicação na porta 5000 (AJUSTAR)
    logging.info("Starting balancer application...")
    app.run(host="0.0.0.0", port=5000)
