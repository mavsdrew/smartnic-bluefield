#!/usr/bin/env python3

from flask import Flask, request, jsonify
from collections import defaultdict
import time, random

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações dos servidores NGINX
SERVERS = ["192.168.1.101", "192.168.1.102", "192.168.1.103"]  # Servidores NGINX
PORT = 80  # Porta padrão para HTTP
strategy = "round_robin"  # Estratégia de balanceamento: "round_robin" ou "least_connections"

# Estado compartilhado
current_server = 0  # Índice do servidor atual (para round_robin)
connections = defaultdict(int)  # Contador de conexões ativas para cada servidor (least_connections)
metrics = defaultdict(lambda: {"requests": 0, "latency": []})  # Métricas por servidor

# Endpoint principal para balanceamento
@app.route('/balance', methods=['POST'])
def balance():
    """
    Recebe requisições HTTP e distribui o fluxo para um dos servidores NGINX
    """
    global current_server  # Necessário para alterar o estado global do índice do servidor

    # Captura o fluxo ID da requisição ou gera um ID aleatório
    flow_id = request.json.get('flow_id', random.randint(1, 100000))
    start_time = time.time()  # Marca o tempo inicial para cálculo da latência
    print(f"Processing flow: {flow_id}")  # Log simples para debug

    # Escolhe o servidor baseado na estratégia configurada
    if strategy == "round_robin":
        server = SERVERS[current_server]  # Escolhe o servidor atual
        current_server = (current_server + 1) % len(SERVERS)  # Avança para o próximo servidor
    elif strategy == "least_connections":
        server = min(SERVERS, key=lambda s: connections[s])  # Servidor com menos conexões
        connections[server] += 1  # Incrementa o número de conexões para este servidor
    else:
        return jsonify({"erro": "Estratégia inválida"}), 400  # Retorna erro se a estratégia não for suportada

    # Atualiza as métricas
    metrics[server]["requests"] += 1
    metrics[server]["latency"].append(time.time() - start_time)

    # Retorna a decisão do balanceamento (servidor e porta)
    return jsonify({"server": server, "porta": PORT, "flow_id": flow_id})

# Endpoint para liberar conexões após término do uso
@app.route('/release', methods=['POST'])
def release_flow():
    """
    Libera uma conexão do servidor especificado no payload da requisição
    """
    server = request.json.get('server')  # IP do servidor que está liberando uma conexão
    if server in connections and connections[server] > 0:
        connections[server] -= 1  # Decrementa o contador de conexões
    return jsonify({"status": "ok"}), 200  # Retorna confirmação

# Endpoint de monitoramento
@app.route('/monitor', methods=['GET'])
def monitor():
    """
    Retorna métricas em tempo real:
    - Número de conexões ativas por servidor
    - Número total de requisições por servidor
    - Latência média por servidor
    """
    monitor_data = {}
    for server, data in metrics.items():
        total_requests = data["requests"]
        avg_latency = sum(data["latency"]) / total_requests if total_requests > 0 else 0
        monitor_data[server] = {
            "active_connections": connections[server],
            "total_requests": total_requests,
            "average_latency": avg_latency,
        }
    return jsonify(monitor_data)

if __name__ == "__main__":
    # Inicia a aplicação na porta 5000 (ajuste se necessário)
    app.run(host="0.0.0.0", port=5000)
