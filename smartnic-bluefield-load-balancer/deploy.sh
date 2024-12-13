#!/bin/bash

# Inicialização do ambiente para balanceamento de carga
# Mensagem inicial
echo "Configuração do ambiente de balanceamento de carga iniciada."

# Verifica se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "Erro: Docker não está instalado. Por favor, instale o Docker antes de executar este script."
    exit 1
fi

# Verifica se o DOCA SDK está instalado
if [ ! -d "/opt/mellanox/doca" ]; then
    echo "Erro: DOCA SDK não encontrado! Certifique-se de que está instalado corretamente."
    exit 1
fi

# Verifica se o arquivo balancer.py existe
if [ ! -f balancer.py ]; then
    echo "Erro: Arquivo balancer.py não encontrado! Certifique-se de que o arquivo está no diretório correto."
    exit 1
fi

# Definição dos contêineres NGINX e seus IPs
NGINX_CONTAINERS=("nginx1" "nginx2" "nginx3")  # Nomes dos contêineres
NGINX_IPS=("192.168.1.101" "192.168.1.102" "192.168.1.103")  # IPs estáticos para os contêineres

# Loop para configurar cada contêiner
for i in ${!NGINX_CONTAINERS[@]}; do
    echo "Iniciando ${NGINX_CONTAINERS[$i]} com IP ${NGINX_IPS[$i]}"
    docker run -d --name ${NGINX_CONTAINERS[$i]} --net=none nginx  # Inicia o contêiner sem rede
    ip link add ${NGINX_CONTAINERS[$i]} type veth peer name ${NGINX_CONTAINERS[$i]}_host  # Cria interface de rede
    ip addr add ${NGINX_IPS[$i]}/24 dev ${NGINX_CONTAINERS[$i]}_host  # Atribui IP à interface
    ip link set ${NGINX_CONTAINERS[$i]}_host up  # Ativa a interface
done

# Configuração de VFs no BlueField
echo "Criando funções virtuais (VFs) no BlueField."
if [ -d "/sys/class/net/enp1s0f0/device/sriov_numvfs" ]; then
    echo 3 > /sys/class/net/enp1s0f0/device/sriov_numvfs
    echo "Funções virtuais criadas com sucesso."
else
    echo "Erro: Interface SR-IOV não encontrada. Certifique-se de que a configuração do BlueField está correta."
    exit 1
fi

# Configuração do DOCA Flow
echo "Iniciando o DOCA Flow para manipulação de tráfego."
if [ -f "/etc/doca_flow_hairpin.cfg" ]; then
    doca_flow_hairpin -c /etc/doca_flow_hairpin.cfg
    echo "DOCA Flow iniciado com sucesso."
else
    echo "Erro: Arquivo de configuração do DOCA Flow (/etc/doca_flow_hairpin.cfg) não encontrado."
    exit 1
fi

# Inicia o balanceador
echo "Iniciando a aplicação balanceadora."
python3 balancer.py &  # Executa a aplicação balanceadora em segundo plano
if [ $? -eq 0 ]; then
    echo "Aplicação balanceadora iniciada com sucesso."
else
    echo "Erro: Falha ao iniciar a aplicação balanceadora."
    exit 1
fi

# Mensagem de conclusão
echo "Configuração concluída! Todos os contêineres e o balanceador estão em execução."
