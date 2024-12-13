# Balanceador de Carga - BlueField SmartNIC

Este projeto demonstra como usar a programabilidade de infraestruturas de rede para distribuir tráfego HTTP entre servidores backend (NGINX) utilizando a SmartNIC BlueField, com suporte para estratégias como `round_robin` e `least_connections`.

---

## Requisitos

1. **Docker**: Para executar os contêineres NGINX.
2. **Python 3.8+**: Para rodar o balanceador.
3. **wrk**: Ferramenta para teste de desempenho.
4. **post.lua**: Script Lua para simular requisições POST personalizadas (ver seção abaixo).

---

## Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/mavsdrew/smartnic-bluefield.git
   cd smartnic-bluefield

# Avaliação de Desempenho do Balanceador

## Teste com `wrk`
Execute o seguinte comando para simular carga no endpoint `/balance`:

```bash
wrk -t12 -c400 -d30s http://192.168.1.100:5000/balance
```

## Teste com `wrk personalizado`
Execute o seguinte comando para simular carga no endpoint `/balance` utilizando um payload personalizado:

```bash
wrk -t12 -c400 -d30s -s post.lua http://192.168.1.100:5000/balance
```