import logging
import doca_flow

def create_hairpin_pipeline(doca_context):
    """
    Cria um pipeline DOCA Flow para encaminhar pacotes entre portas físicas.

    Parâmetros:
    - doca_context: Contexto DOCA Flow inicializado.

    Retorna:
    - ID do pipeline criado (ou None em caso de erro).
    """
    try:
        # Configuração do match (correspondência) para os pacotes
        match = {
            "outer_l4_type": "UDP",       # Tipo de transporte (UDP)
            "outer_l3_type": "IPV4",      # Tipo de camada de rede (IPv4)
            "src_ip": "0.0.0.0",          # Qualquer IP de origem
            "dst_ip": "255.255.255.255",  # Qualquer IP de destino
            "src_port": 0,                # Qualquer porta de origem
            "dst_port": 65535             # Qualquer porta de destino
        }

        # Configuração de encaminhamento (forwarding)
        fwd = {
            "type": "port",      # Encaminhamento para uma porta física
            "port_id": 1         # Porta física de destino (ajuste conforme necessário)
        }

        # Adiciona o pipeline no DOCA Flow
        pipe_id = doca_flow.add_pipeline(doca_context, match, fwd)
        logging.info(f"Hairpin pipeline created with ID {pipe_id}")
        return pipe_id

    except Exception as e:
        logging.error(f"Failed to create Hairpin pipeline: {e}")
        return None
