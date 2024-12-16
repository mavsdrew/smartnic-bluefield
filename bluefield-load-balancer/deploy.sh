#!/bin/bash

# Inicialização do ambiente para balanceamento de carga
echo "Configuração do ambiente de balanceamento de carga iniciada."

# ******************************************************
# Configurações de Variáveis
INTERFACE="enp1s0f0"  # Interface
NGINX_CONTAINERS=("nginx1" "nginx2" "nginx3")  # Nomes dos contêineres
NGINX_IPS=("192.168.1.101" "192.168.1.102" "192.168.1.103")  # IPs estáticos para os contêineres

BALANCER_SCRIPT="balancer.py"  # Nome do arquivo principal do balanceador
DOCA_CONFIG="/etc/doca_flow_hairpin.cfg"  # Arquivo de configuração do DOCA Flow
DOCA_SDK_PATH="/opt/mellanox/doca"  # Caminho do DOCA SDK
# ******************************************************

# Verifica dependências
echo "Verificando dependências..."
if ! command -v dpdk-devbind &> /dev/null; then
    echo "Erro: dpdk-devbind não encontrado. Instale o DPDK."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Erro: Python 3 não encontrado."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado. Por favor, instale o Docker antes de executar este script."
    exit 1
fi

if [ ! -d "$DOCA_SDK_PATH" ]; then
    echo "Erro: DOCA SDK não encontrado! Certifique-se de que está instalado corretamente em $DOCA_SDK_PATH."
    exit 1
fi

if [ ! -f "$BALANCER_SCRIPT" ]; then
    echo "Erro: Arquivo $BALANCER_SCRIPT não encontrado! Certifique-se de que está no diretório correto."
    exit 1
fi

# Configurações do DPDK
echo "Configurando DPDK..."
sudo dpdk-devbind --bind=mlx5_core $INTERFACE

# Configuração de VFs no BlueField
echo "Criando funções virtuais (VFs) no BlueField..."
if [ -d "/sys/class/net/$INTERFACE/device/sriov_numvfs" ]; then
    echo 3 > "/sys/class/net/$INTERFACE/device/sriov_numvfs"
    echo "Funções virtuais criadas com sucesso."
else
    echo "Erro: Interface SR-IOV não encontrada para $INTERFACE. Certifique-se de que a configuração está correta."
    exit 1
fi

# Configuração dos contêineres NGINX
echo "Configurando contêineres NGINX..."
# Loop para configurar cada contêiner
for i in ${!NGINX_CONTAINERS[@]}; do
    echo "Iniciando contêiner ${NGINX_CONTAINERS[$i]} com IP ${NGINX_IPS[$i]}"

    # Inicia o contêiner
    docker run -d --name ${NGINX_CONTAINERS[$i]} --net=none nginx  # Inicia o contêiner sem rede
    if [ $? -ne 0 ]; then
        echo "Erro ao iniciar o contêiner ${NGINX_CONTAINERS[$i]}"
        exit 1
    fi

    # Configura interface de rede
    ip link add ${NGINX_CONTAINERS[$i]} type veth peer name ${NGINX_CONTAINERS[$i]}_host  # Cria interface de rede
    ip addr add ${NGINX_IPS[$i]}/24 dev ${NGINX_CONTAINERS[$i]}_host  # Atribui IP à interface
    ip link set ${NGINX_CONTAINERS[$i]}_host up  # Ativa a interface
done

# Configuração do DOCA Flow
echo "Iniciando o DOCA Flow para manipulação de tráfego..."
if [ -f "$DOCA_CONFIG" ]; then
    doca_flow_hairpin -c "$DOCA_CONFIG"
    if [ $? -ne 0 ]; then
        echo "Erro ao iniciar o DOCA Flow com o arquivo de configuração $DOCA_CONFIG."
        exit 1
    fi
    echo "DOCA Flow iniciado com sucesso."
else
    echo "Erro: Arquivo de configuração do DOCA Flow ($DOCA_CONFIG) não encontrado."
    exit 1
fi

# Inicia o balanceador
echo "Iniciando a aplicação balanceadora..."
nohup python3 $BALANCER_SCRIPT > balancer.log 2>&1 &
if [ $? -eq 0 ]; then
    echo "Aplicação balanceadora iniciada com sucesso."
else
    echo "Erro: Falha ao iniciar a aplicação balanceadora."
    exit 1
fi

# Mensagem de conclusão
echo "Configuração concluída! Todos os contêineres e o balanceador estão em execução."
