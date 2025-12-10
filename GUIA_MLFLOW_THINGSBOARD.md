# 📘 Guia: MLflow e ThingsBoard - Versionamento e Visualização

## 📋 Visão Geral

Este guia explica como usar as funcionalidades de **versionamento de modelos com MLflow** e **visualização de dados com ThingsBoard** no HubFólio.

---

## 🎯 1. MLflow - Versionamento de Modelos

### O que é MLflow?

O **MLflow** é uma plataforma open-source para gerenciar o ciclo de vida de modelos de Machine Learning, incluindo:

- ✅ **Rastreamento de experimentos** - Registra métricas, parâmetros e artefatos
- ✅ **Model Registry** - Versionamento e gerenciamento de modelos
- ✅ **Reproducibilidade** - Permite reproduzir experimentos anteriores
- ✅ **Deploy** - Facilita o deploy de modelos em produção

### Acessando o MLflow

Após subir os containers, acesse:

**URL:** http://localhost:5000

Você verá a interface do MLflow com:
- Lista de experimentos
- Runs (execuções) de treinamento
- Modelos registrados
- Métricas e parâmetros

---

## 🚀 2. Como Usar o MLflow no HubFólio

### Passo 1: Fazer Upload do Modelo com Versionamento

Quando você faz upload de um modelo via API, ele é automaticamente registrado no MLflow:

```bash
# Via Swagger UI (Recomendado)
# Acesse: http://localhost:8001/docs
# Endpoint: POST /model/upload
```

**Parâmetros opcionais:**

- `model_name`: Nome do modelo no MLflow (padrão: "hubfolio-model")
- `r2_score`: R² score do modelo
- `rmse`: RMSE do modelo
- `mae`: MAE do modelo
- `register_in_mlflow`: Se True, registra no MLflow (padrão: True)
- `export_to_s3`: Se True, exporta para S3 após registro (padrão: True)

**Exemplo via curl:**

```bash
curl -X POST "http://localhost:8001/model/upload" \
  -F "file=@models/hubfolio_model.pkl" \
  -F "model_name=hubfolio-model" \
  -F "r2_score=0.85" \
  -F "rmse=12.5" \
  -F "mae=9.2"
```

**Resposta esperada:**

```json
{
  "message": "Modelo carregado com sucesso!",
  "model_path": "/app/models/hubfolio_model.pkl",
  "file_size": 755,
  "mlflow_registered": true,
  "mlflow_run_id": "abc123def456",
  "mlflow_model_version": "1",
  "s3_exported": true,
  "s3_key": "models/hubfolio-model/v1/hubfolio-model_v1_20250115_120000.pkl"
}
```

### Passo 2: Verificar Modelo no MLflow

1. Acesse http://localhost:5000
2. Clique em **"Experiments"** → **"hubfolio-models"**
3. Veja os runs (execuções) com métricas e parâmetros
4. Clique em **"Models"** para ver modelos registrados

### Passo 3: Exportar Modelo do MLflow para S3

Você pode exportar manualmente um modelo do MLflow para o S3:

```bash
# Via API
curl -X POST "http://localhost:8001/model/export-to-s3" \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "hubfolio-model",
    "stage": "Production"
  }'
```

**Resposta esperada:**

```json
{
  "message": "Modelo exportado para S3 com sucesso!",
  "model_name": "hubfolio-model",
  "stage": "Production",
  "s3_key": "models/hubfolio-model/v1/hubfolio-model_v1_20250115_120000.pkl"
}
```

### Passo 4: Verificar Informações do Modelo

```bash
curl http://localhost:8001/model/info
```

**Resposta esperada:**

```json
{
  "model_loaded": true,
  "model_name": "LinearRegression",
  "features": ["projetos_min", "habilidades_min", ...],
  "num_features": 8,
  "mlflow": {
    "name": "hubfolio-model",
    "latest_versions": [
      {
        "version": "1",
        "stage": "Production",
        "run_id": "abc123def456",
        "created_at": "2025-01-15T12:00:00"
      }
    ],
    "created_at": "2025-01-15T12:00:00"
  }
}
```

---

## 📊 3. ThingsBoard - Visualização de Dados

### O que é ThingsBoard?

O **ThingsBoard** é uma plataforma open-source para visualização de dados IoT e telemetria, permitindo:

- ✅ **Dashboards interativos** - Visualizações em tempo real
- ✅ **Telemetria** - Recebe dados de dispositivos/serviços
- ✅ **Alertas** - Configuração de alertas baseados em métricas
- ✅ **Análise** - Análise de tendências e padrões

### Acessando o ThingsBoard

Após subir os containers, acesse:

**URL:** http://localhost:8080

**Credenciais padrão:**
- Username: `tenant@thingsboard.org`
- Password: `tenant`

> **Nota:** O ThingsBoard pode levar alguns minutos para inicializar completamente.

---

## 🚀 4. Como Usar o ThingsBoard no HubFólio

### Passo 1: Configurar Dispositivo no ThingsBoard

1. Acesse http://localhost:8080
2. Faça login com as credenciais padrão
3. Vá em **"Devices"** → **"Add device"**
4. Crie um dispositivo chamado **"HubFólio Predictions"**
5. Copie o **Device Token** (ex: `hubfolio-device-token`)

### Passo 2: Configurar Token no Docker Compose

Edite o `docker-compose.yml` e adicione o token:

```yaml
environment:
  THINGSBOARD_DEVICE_TOKEN: seu-device-token-aqui
```

Ou configure via variável de ambiente:

```bash
export THINGSBOARD_DEVICE_TOKEN=seu-device-token-aqui
```

### Passo 3: Enviar Dados Automaticamente

Quando você faz uma predição via API, os dados são **automaticamente enviados** para o ThingsBoard:

```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "projetos_min": 3,
    "habilidades_min": 10,
    "kw_contexto": 4,
    "kw_processo": 3,
    "kw_resultado": 4,
    "consistencia_visual_score": 80,
    "bio": true,
    "contatos": true
  }'
```

Os seguintes dados são enviados automaticamente:
- `predicted_iq`: Índice de Qualidade previsto
- `portfolio_id`: ID do portfólio
- `model_name`: Nome do modelo usado
- `classification`: Classificação (Excelente, Bom, etc.)
- `user_id`: ID do usuário
- `prediction_id`: ID da predição

### Passo 4: Criar Dashboard no ThingsBoard

1. Acesse **"Dashboards"** → **"Add dashboard"**
2. Crie um dashboard chamado **"HubFólio Analytics"**
3. Adicione widgets:
   - **Time series chart** para `predicted_iq`
   - **Gauge** para mostrar IQ médio
   - **Table** para listar predições recentes
   - **Pie chart** para distribuição de classificações

### Passo 5: Visualizar Dados em Tempo Real

Após criar o dashboard, você verá:
- 📈 Gráficos de IQ ao longo do tempo
- 📊 Distribuição de classificações
- 📋 Tabela com predições recentes
- 🎯 Métricas agregadas

---

## 🔧 5. Configuração Avançada

### Variáveis de Ambiente

Configure as seguintes variáveis no `docker-compose.yml`:

```yaml
environment:
  # MLflow
  MLFLOW_TRACKING_URI: http://mlflow:5000
  MLFLOW_S3_ENDPOINT_URL: http://minio:9000
  MLFLOW_EXPERIMENT_NAME: hubfolio-models
  
  # ThingsBoard
  THINGSBOARD_URL: http://thingsboard:9090
  THINGSBOARD_DEVICE_TOKEN: hubfolio-device-token
  THINGSBOARD_USERNAME: tenant@thingsboard.org
  THINGSBOARD_PASSWORD: tenant
```

### Verificar Status dos Serviços

```bash
# Verificar saúde da API
curl http://localhost:8001/health
```

**Resposta esperada:**

```json
{
  "status": "healthy",
  "minio_connected": true,
  "bucket_exists": true,
  "postgres_connected": true,
  "mlflow_connected": true,
  "thingsboard_connected": true,
  "timestamp": "2025-01-15T12:00:00"
}
```

---

## 📝 6. Fluxo Completo

### Pipeline Completo de Modelo

```
1. Treinar modelo no Jupyter Notebook
   ↓
2. Exportar modelo como .pkl
   ↓
3. Upload via POST /model/upload
   ↓
4. Modelo registrado no MLflow (com métricas)
   ↓
5. Modelo exportado para S3 (MinIO)
   ↓
6. Modelo disponível para predições
```

### Pipeline Completo de Predição

```
1. Fazer predição via POST /predict
   ↓
2. Predição salva no PostgreSQL
   ↓
3. Dados enviados para ThingsBoard (telemetria)
   ↓
4. Dashboard atualizado em tempo real
   ↓
5. Visualizações e insights disponíveis
```

---

## 🐛 7. Troubleshooting

### MLflow não conecta

```bash
# Verificar se o container está rodando
docker-compose ps mlflow

# Ver logs
docker-compose logs mlflow

# Verificar se a porta está acessível
curl http://localhost:5000
```

### ThingsBoard não conecta

```bash
# Verificar se o container está rodando
docker-compose ps thingsboard

# Ver logs (pode levar alguns minutos para inicializar)
docker-compose logs -f thingsboard

# Verificar se a porta está acessível
curl http://localhost:8080
```

### Dados não aparecem no ThingsBoard

1. Verifique se o **Device Token** está correto
2. Verifique se o dispositivo foi criado no ThingsBoard
3. Verifique os logs da API:

```bash
docker-compose logs -f fastapi | grep ThingsBoard
```

### Modelo não exporta para S3

1. Verifique se o MLflow está conectado
2. Verifique se o MinIO está acessível
3. Verifique as credenciais do S3 no `docker-compose.yml`

---

## 📚 8. Recursos Adicionais

### Documentação Oficial

- **MLflow:** https://mlflow.org/docs/latest/index.html
- **ThingsBoard:** https://thingsboard.io/docs/

### Endpoints da API

- `POST /model/upload` - Upload e registro no MLflow
- `POST /model/export-to-s3` - Exportar modelo para S3
- `GET /model/info` - Informações do modelo e MLflow
- `POST /predict` - Predição (envia dados para ThingsBoard)
- `GET /health` - Status de todos os serviços

---

## ✅ Checklist de Implementação

- [x] MLflow configurado no docker-compose.yml
- [x] Cliente MLflow implementado
- [x] Integração com endpoint de upload
- [x] Exportação automática para S3
- [x] ThingsBoard configurado no docker-compose.yml
- [x] Cliente ThingsBoard implementado
- [x] Integração com endpoint de predição
- [x] Envio automático de telemetria
- [x] Documentação completa

---

## 🎓 Resumo

**MLflow:**
- ✅ Versionamento automático de modelos
- ✅ Registro de métricas e parâmetros
- ✅ Exportação para S3 (MinIO)
- ✅ Interface web para visualização

**ThingsBoard:**
- ✅ Recebimento automático de predições
- ✅ Dashboards interativos
- ✅ Visualizações em tempo real
- ✅ Análise de tendências

**Fluxo Integrado:**
1. Modelo → MLflow → S3
2. Predição → PostgreSQL → ThingsBoard
3. Visualização → Dashboard → Insights

---

**Pronto!** Agora você tem um pipeline completo de versionamento e visualização! 🚀

