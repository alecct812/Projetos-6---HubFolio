# 🔧 Correções Aplicadas

## Problema: Porta 5000 em Uso

A porta 5000 estava sendo usada por outro processo (provavelmente AirPlay Receiver no macOS).

### Solução Aplicada

✅ **MLflow agora usa a porta 5001** no host (mapeamento: `5001:5000`)

- **Internamente no Docker**: MLflow roda na porta 5000 (como sempre)
- **Externamente (host)**: Acesse via `http://localhost:5001`

### Como Acessar

- **MLflow UI**: http://localhost:5001 (ao invés de 5000)
- **API Interna**: Continua usando `http://mlflow:5000` dentro do Docker

### Aviso sobre `version`

O aviso sobre `version` obsoleto ainda aparece porque:
- O Docker Compose pode estar usando cache
- O arquivo já foi corrigido (sem `version`)

Para limpar o cache:
```bash
docker-compose down
docker system prune -f
docker-compose up -d --build
```

---

## Status dos Serviços

Após executar `docker-compose up -d --build`, você deve ter:

- ✅ **MinIO**: http://localhost:9101 (console)
- ✅ **PostgreSQL**: localhost:5433
- ✅ **MLflow**: http://localhost:5001 (UI)
- ✅ **FastAPI**: http://localhost:8001 (API)

---

## Próximos Passos

1. Execute: `docker-compose up -d --build`
2. Verifique: `docker-compose ps`
3. Acesse MLflow: http://localhost:5001
4. Teste a API: http://localhost:8001/docs

