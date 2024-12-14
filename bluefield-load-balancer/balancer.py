#!/usr/bin/env python3

# Importação de bibliotecas
from flask import Flask, request, jsonify  # Flask para criar APIs, request para lidar com dados de entrada, jsonify para formatar respostas em JSON
from collections import defaultdict  # Usado para criar dicionários com valores padrão
import os  # Para obter variáveis de ambiente
import time  # Para medir o tempo (latência)
import random  # Para gerar IDs aleatórios
import logging  # Para registrar eventos e informações de debug
import doca_flow  # Biblioteca para manipular pacotes com BlueField

# Configura o logging para rastrear operações do balanceador
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações dos servidores NGINX
# Lidas de variáveis de ambiente para flexibilidade
SERVERS = os.getenv("SERVERS", "192.168.1.101,192.168.1.102,192.168.1.103").split(",")
PORT = int(os.getenv("PORT", 80))  # Porta padrão para HTTP e configurável
STRATEGY = os.getenv("STRATEGY", "round_robin")  # Estratégia de balanceamento: "round_robin" ou "least_connections"

# Estado compartilhado do balanceador
current_server = 0  # Índice do servidor atual (para round_robin)
connections = defaultdict(int)  # Contador de conexões ativas para cada servidor (least_connections)
metrics = defaultdict(lambda: {"requests": 0, "latency": []})  # Métricas como número de requisições e latências

# Inicializa o DOCA Flow
try:
    doca_context = doca_flow.init("balanceador", {})  # Contexto DOCA inicializado
    logging.info("DOCA Flow initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing DOCA Flow: {e}")
    exit(1)

# ******************************************************
# Função para criar um pipeline DOCA Flow com Hairpin
def create_hairpin_pipeline(doca_context):
    """
    Cria um pipeline DOCA Flow para encaminhar pacotes entre portas físicas.
    """
    try:
        match = {
            "outer_l4_type": "UDP",
            "outer_l3_type": "IPV4",
            "src_ip": "0.0.0.0",
            "dst_ip": "255.255.255.255",
            "src_port": 0,
            "dst_port": 65535
        }
        fwd = {"type": "port", "port_id": 1}
        pipe_id = doca_flow.add_pipeline(doca_context, match, fwd)
        logging.info(f"Hairpin pipeline created with ID {pipe_id}")
        return pipe_id
    except Exception as e:
        logging.error(f"Failed to create hairpin pipeline: {e}")
        return None

# Função para criar um pipeline DOCA Flow com RSS e metadados
def create_rss_meta_pipeline(doca_context):
    """
    Cria um pipeline DOCA Flow para manipular tráfego com RSS e metadados.
    """
    try:
        match = {
            "outer_l4_type": "UDP",
            "outer_l3_type": "IPV4",
            "src_ip": "0.0.0.0",
            "dst_ip": "255.255.255.255",
            "src_port": 0,
            "dst_port": 65535
        }
        actions = {"meta": {"pkt_meta": 10}}
        rss_config = {
            "type": "RSS",
            "rss_queues": [0],  # Exemplo com a fila 0
            "rss_inner_flags": ["IPV4", "UDP"]
        }
        pipe_id = doca_flow.add_pipeline(doca_context, match, actions, rss_config)
        logging.info(f"RSS Meta pipeline created with ID {pipe_id}")
        return pipe_id
    except Exception as e:
        logging.error(f"Failed to create RSS Meta pipeline: {e}")
        return None
# ******************************************************

# Middleware para configurar timeout para requisições Flask
@app.before_request
def set_timeout():
    request.environ['werkzeug.request_timeout'] = 10  # Timeout de 10 segundos

# Endpoint principal para balanceamento de carga
@app.route('/balance', methods=['POST'])
def balance():
    """
    Recebe requisições HTTP e distribui o fluxo para um dos servidores NGINX
    """
    global current_server  # Necessário para alterar o estado global do índice do servidor

    # Valida o payload recebido
    if not request.json or "flow_id" not in request.json:
        return jsonify({"error": "Invalid request. Missing 'flow_id'"}), 400
    
    # Captura o ID do fluxo ou gera um novo ID aleatório
    flow_id = request.json.get('flow_id', random.randint(1, 100000))
    start_time = time.time()  # Marca o tempo inicial para cálculo da latência
    logging.info(f"Processing flow {flow_id}.")  # Log simples para debug

    # Escolhe o servidor baseado na estratégia configurada
    if STRATEGY == "round_robin":
        server = SERVERS[current_server]  # Escolhe o servidor atual (servidor atual no índice)
        current_server = (current_server + 1) % len(SERVERS)  # Avança para o próximo servidor no round-robin
    elif STRATEGY == "least_connections":
        server = min(SERVERS, key=lambda s: connections[s])  # Escolhe o servidor com menos conexões
        connections[server] += 1  # Incrementa o número de conexões para este servidor
    # ******************************************************
    elif STRATEGY == "hairpin":
        pipe_id = create_hairpin_pipeline(doca_context)
        if not pipe_id:
            return jsonify({"error": "Failed to create Hairpin pipeline"}), 500
        return jsonify({"strategy": "hairpin", "pipeline_id": pipe_id})
    elif STRATEGY == "rss_meta":
        pipe_id = create_rss_meta_pipeline(doca_context)
        if not pipe_id:
            return jsonify({"error": "Failed to create RSS Meta pipeline"}), 500
        return jsonify({"strategy": "rss_meta", "pipeline_id": pipe_id})
    # ******************************************************
    else:
        return jsonify({"error": "Invalid strategy. Supported strategies are 'round_robin' and 'least_connections'."}), 400  # Retorna erro se a estratégia não for suportada

    # Configura o fluxo no DOCA para manipulação no BlueField
    try:
        rule_id = doca_flow.add_rule(doca_context, {"server_ip": server, "port": PORT})
        if rule_id is None:
            raise Exception("Rule ID is None")
    except Exception as e:
        logging.error(f"Error adding DOCA Flow rule: {e}")
        return jsonify({"error": "Failed to add flow to DOCA."}), 500

    # Atualiza as métricas do servidor
    metrics[server]["requests"] += 1  # Incrementa o número de requisições
    metrics[server]["latency"].append(time.time() - start_time)  # Calcula a latência da requisição
    logging.info(f"Flow {flow_id} directed to server {server} using {STRATEGY} strategy.")  # Log da decisão do balanceador

    # Retorna a decisão de balanceamento
    return jsonify({"server": server, "porta": PORT, "flow_id": flow_id})

# Endpoint para liberar conexões após término do uso
@app.route('/release', methods=['POST'])
def release_flow():
    """
    Libera uma conexão do servidor especificado na requisição
    """
    # Valida o payload
    if not request.json or "server" not in request.json:
        return jsonify({"error": "Invalid request. Missing 'server'"}), 400
    
    # Obtém o servidor a partir do payload
    server = request.json.get('server')  # IP do servidor que está liberando uma conexão

    # Valida se o servidor está na lista configurada
    if server not in SERVERS:
        return jsonify({"error": f"Server {server} is not in the server list."}), 400

    # Decrementa o número de conexões para o servidor
    if server in connections and connections[server] > 0:
        connections[server] -= 1  # Decrementa o contador de conexões
        logging.info(f"Connection released from server {server}.")
    else:
        logging.warning(f"Release request for server {server}, but no active connections found.")

    return jsonify({"status": "ok"}), 200  # Retorna confirmação

# Endpoint de monitoramento
@app.route('/monitor', methods=['GET'])
def monitor():
    """
    Retorna métricas em tempo real para cada servidor:
    - Número de conexões ativas
    - Número total de requisições
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
    
    logging.info(f"Monitor metrics retrieved: {monitor_data}")  # Log do evento de monitoramento
    return jsonify(monitor_data)

# Inicializa a aplicação Flask
if __name__ == "__main__":
    logging.info(f"Starting balancer application on port {PORT}...")
    try:
        app.run(host="0.0.0.0", port=PORT)
    except Exception as e:
        logging.error(f"Failed to start the application: {e}")
        exit(1)
