# Balanceador de Carga - SmartNIC BlueField

Este projeto demonstra como usar a programabilidade de infraestruturas de rede para distribuir tráfego HTTP entre servidores backend (NGINX) utilizando a SmartNIC BlueField, com suporte para estratégias como `round_robin` e `least_connections`.

Este balanceador melhora o desempenho ao offloadar o processamento de pacotes HTTP para a SmartNIC BlueField, permitindo maior escalabilidade e flexibilidade.


---

## Requisitos

1. **Docker**: Para executar os contêineres NGINX.
2. **Python 3.8+**: Para rodar o balanceador.
3. **wrk**: Ferramenta para teste de desempenho.
4. **post.lua**: Script Lua para simular requisições POST personalizadas (ver seção abaixo).
5. **DOCA SDK**: Necessário para integração com a SmartNIC BlueField.

---

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/mavsdrew/smartnic-bluefield.git
   cd bluefield-load-balancer

## Configuração do Ambiente Nvidia BlueField

1. **Configuração do DOCA:**
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

2. **Configuração do BlueField:**
   - Ative as funções virtuais (VFs) no BlueField:
     ```bash
     echo 3 > /sys/class/net/<interface>/device/sriov_numvfs
     ```
     Substitua `<interface>` pelo nome da interface de rede conectada ao BlueField, como `enp1s0f0`.

3. **Configuração do DOCA Flow:**
   - Crie um arquivo de configuração para o DOCA Flow:
     ```bash
     vim /etc/doca_flow_hairpin.cfg
     ```
     Adicione o seguinte conteúdo:
     ```
     [hairpin]
     pipeline = true
     ```
     Este arquivo define como o DOCA irá processar os pacotes de rede usando pipelines no modo hairpin.
   - Inicie o DOCA Flow:
     ```bash
     doca_flow_hairpin -c /etc/doca_flow_hairpin.cfg
     ```

4. **Executar o Balanceador:**
   - Inicie o balanceador com o script `deploy.sh`:
     ```bash
     bash deploy.sh
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

Este projeto demonstra como integrar DOCA Flow com balanceamento HTTP em um ambiente SmartNIC Nvidia BlueField, aproveitando sua capacidade de programabilidade. As instruções fornecidas devem permitir a instalação, configuração e testes de desempenho completos.
