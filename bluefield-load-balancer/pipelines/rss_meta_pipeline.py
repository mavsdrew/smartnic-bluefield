import logging
import doca_flow

def create_rss_meta_pipeline(doca_context):
    """
    Cria um pipeline DOCA Flow para manipular tráfego com RSS e metadados.

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

        # Configuração de ações (actions)
        actions = {
            "meta": {
                "pkt_meta": 10  # Adiciona um valor de metadado ao pacote
            }
        }

        # Configuração de RSS (Receive Side Scaling)
        rss_config = {
            "type": "RSS",                  # Tipo RSS
            "rss_queues": [0, 1, 2, 3],     # Filas RSS disponíveis
            "rss_inner_flags": ["IPV4", "UDP"]  # Flags para correspondência interna
        }

        # Adiciona o pipeline no DOCA Flow
        pipe_id = doca_flow.add_pipeline(doca_context, match, actions, rss_config)
        logging.info(f"RSS Meta pipeline created with ID {pipe_id}")
        return pipe_id

    except Exception as e:
        logging.error(f"Failed to create RSS Meta pipeline: {e}")
        return None
