# **Balanceador de Carga - SmartNIC BlueField**

Este projeto demonstra como usar a programabilidade de infraestruturas de rede para distribuir tráfego HTTP entre servidores backend (NGINX) utilizando a SmartNIC BlueField, com suporte para estratégias como `round_robin`, `least_connections`, `rss_meta` e `hairpin`.

Este balanceador melhora o desempenho ao offloadar o processamento de pacotes HTTP para a SmartNIC BlueField, permitindo maior escalabilidade e flexibilidade.

---

## **Requisitos**

1. **Docker**: Para executar os contêineres NGINX.
2. **Python 3.8+**: Para rodar o balanceador.
3. **wrk**: Ferramenta para teste de desempenho.
4. **post.lua**: Script Lua para simular requisições POST personalizadas (ver seção abaixo).
5. **DOCA SDK**: Necessário para integração com a SmartNIC BlueField.
6. **DPDK**: Para configuração de interfaces da SmartNIC.

---

## **Estrutura de Diretórios**

```plaintext
bluefield-load-balancer/
├── balancer.py                   # Arquivo principal do balanceador
├── deploy.sh                     # Script para configurar e implantar o ambiente
├── pipelines/                    # Diretório para pipelines DOCA Flow
│   ├── __init__.py               # Arquivo para inicializar o pacote pipelines
│   ├── hairpin_pipeline.py       # Código para criar pipelines Hairpin
│   ├── rss_meta_pipeline.py      # Código para criar pipelines RSS com metadados
├── requirements.txt              # Dependências do projeto
├── README.md                     # Documentação do projeto
├── .gitignore                    # Arquivo para ignorar arquivos/diretórios no Git
```

---

## Instalação

1. Clone o repositório:
    ```bash
    git clone https://github.com/mavsdrew/smartnic-bluefield.git
    cd bluefield-load-balancer
    ```

2. Instale as dependências:
  - Utilize um ambiente virtual para instalar as dependências:
    ```bash
    python3 -m venv venv  
    source venv/bin/activate
    pip install -r requirements.txt
    ```

## Configuração do Ambiente Nvidia BlueField

  - Instale o SDK DOCA:
    ```bash
    wget https://developer.download.nvidia.com/doca/<sdk_version>.tar.gz
    tar -xvf <sdk_version>.tar.gz
    cd <sdk_version>
    ./install.sh
    ```
  - Certifique-se de que o DOCA Flow está funcionando:
    ```bash
    doca_flow -h
    ```
## Execute o Script de Implantação:
  - Use o script deploy.sh para configurar o ambiente completo:
    ```bash
    bash deploy.sh
    ```

# Execução

Após a configuração, o balanceador estará disponível na porta 80. Você pode interagir com os seguintes endpoints:

## Endpoints Disponíveis
  
1. /balance (POST):
  - Redireciona fluxos para os servidores backend com base na estratégia configurada.
  - Exemplo de payload:
    ```json
    {
      "flow_id": 12345
    }
    ```
  
2. /monitor (GET):
  - Retorna métricas de desempenho em tempo real para cada servidor.
  - Exemplo de saída:
    ```json
    {
      "192.168.1.101": {
          "active_connections": 5,
          "total_requests": 120,
          "average_latency": 0.023,
          "max_latency": 0.045,
          "min_latency": 0.010
      }
    }
    ```

# Avaliação de Desempenho do Balanceador

## Teste com `wrk`
Execute o seguinte comando para simular carga no endpoint `/balance` com requisições padrão GET:

```bash
wrk -t12 -c400 -d30s http://<ip_do_balanceador>:<porta>/balance
```

## Teste com `wrk personalizado`
Execute o seguinte comando para simular carga no endpoint `/balance` utilizando um payload personalizado:

```bash
wrk -t12 -c400 -d30s -s post.lua http://<ip_do_balanceador>:<porta>/balance
```

### Parâmetros Utilizados:
- `-t12`: Usa 12 threads para enviar as requisições.
- `-c400`: Mantém 400 conexões simultâneas durante o teste.
- `-d30s`: Executa o teste por 30 segundos.
- `-s post.lua`: Utiliza o script Lua `post.lua` para enviar requisições POST com um payload personalizado.

**Observação**: Para Desenvolvimento e Testes Locais, use a porta 5000, pois facilita o teste e não requer permissões elevadas. Para Produção, use a porta padrão 80. Neste trabalho, usamos a porta padrão 80.

## Conclusão

Este projeto demonstra como integrar DOCA Flow com balanceamento HTTP em um ambiente SmartNIC Nvidia BlueField. As instruções fornecidas permitem a instalação, configuração e testes de desempenho completos.
