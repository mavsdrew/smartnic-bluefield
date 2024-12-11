#!/usr/bin/env python3

from flask import Flask, request, jsonify
from collections import defaultdict
import random

# Inicializa a aplicação Flask
app = Flask(__name__)

# Configurações dos servidores NGINX (ajustar para os IPs reais do ambiente)
SERVIDORES = ["192.168.1.101", "192.168.1.102", "192.168.1.103"]  # Substituir pelos IPs do ambiente real
PORTA = 80  # Porta padrão para HTTP
estrategia = "round_robin"  # Estratégia de balanceamento: "round_robin" ou "least_connections"

# Estado compartilhado para manter informações de balanceamento
current_server = 0  # Índice do servidor atual (para round-robin)
connections = defaultdict(int)  # Contador de conexões ativas para cada servidor (least_connections)

# Endpoint principal para balanceamento de carga
@app.route('/balancear', methods=['POST'])
def balancear():
    """
    Recebe requisições HTTP e distribui o fluxo para um dos servidores NGINX
    """
    global current_server  # Necessário para alterar o estado global do índice do servidor

    # Captura o fluxo ID da requisição ou gera um ID aleatório
    fluxo_id = request.json.get('fluxo_id', random.randint(1, 100000))
    print(f"Processando fluxo: {fluxo_id}")  # Log simples para debug

    # Escolhe o servidor baseado na estratégia configurada
    if estrategia == "round_robin":
        servidor = SERVIDORES[current_server]  # Escolhe o servidor atual
        current_server = (current_server + 1) % len(SERVIDORES)  # Avança para o próximo servidor
    elif estrategia == "least_connections":
        servidor = min(SERVIDORES, key=lambda s: connections[s])  # Servidor com menos conexões
        connections[servidor] += 1  # Incrementa o número de conexões para este servidor
    else:
        return jsonify({"erro": "Estratégia inválida"}), 400  # Retorna erro se a estratégia não for suportada

    # Retorna a decisão do balanceamento (servidor e porta)
    return jsonify({"servidor": servidor, "porta": PORTA, "fluxo_id": fluxo_id})

# Endpoint para liberar conexões após término do uso
@app.route('/release', methods=['POST'])
def liberar_fluxo():
    """
    Libera uma conexão do servidor especificado no payload da requisição
    """
    servidor = request.json.get('servidor')  # IP do servidor que está liberando uma conexão
    if servidor in connections and connections[servidor] > 0:
        connections[servidor] -= 1  # Decrementa o contador de conexões
    return jsonify({"status": "ok"}), 200  # Retorna confirmação

if __name__ == "__main__":
    # Inicia a aplicação na porta 5000 (ajuste se necessário)
    app.run(host="0.0.0.0", port=5000)
