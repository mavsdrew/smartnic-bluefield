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
