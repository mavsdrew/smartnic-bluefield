#!/bin/bash

# Inicialização do ambiente para balanceamento de carga
# Mensagem inicial
echo "Configuração do ambiente de balanceamento de carga."

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

# Configuração da DOCA (AJUSTE NECESSÁRIO)
echo "Configurando DOCA para manipular tráfego."
# Configurar funções virtuais (VFs) ou outras interfaces da DOCA (conforme a documentação do BlueField):
# doca_setup_vfs.sh --num_vfs=3 --pci=0000:00:00.0

# Inicia a implantação do balanceador
echo "Iniciando aplicação balanceadora."
python3 balancer.py &  # Executa a aplicação balanceadora em segundo plano (verificar se o arquivo consta no diretório correto)
