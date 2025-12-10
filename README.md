# HubFólio - Pipeline de Machine Learning para Análise de Portfólios

Sistema completo de análise e predição de qualidade de portfólios para estudantes de Design e Ciência da Computação.

## Arquitetura

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   FastAPI   │───►│    MinIO    │───►│  PostgreSQL │───►│  ThingsBoard│
│  (Ingestão) │    │ (Storage S3)│    │   (Banco)   │    │ (Dashboard) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                                     │
       │              ┌─────────────┐        │
       └─────────────►│   MLflow    │◄───────┘
                      │(Experimentos)│
                      └─────────────┘
```

## Pré-requisitos

- **Docker Desktop** (Windows/Mac) ou **Docker + Docker Compose** (Linux)
- **Python 3.10+** (para rodar o notebook e scripts de teste)
- **Git** (para clonar o repositório)

### Dependências do Notebook

```bash
pip install -r notebooks/requirements-notebook.txt
```

## Instalação e Execução

### Passo 1: Clonar o Repositório

```bash
git clone <URL_DO_REPOSITORIO>
cd Projetos-6---HubFolio
```

### Passo 2: Subir os Containers

```bash
docker-compose up -d
```

Este comando irá iniciar 5 serviços:

- **MinIO** (porta 9100/9101) - Armazenamento S3
- **PostgreSQL** (porta 5433) - Banco de dados
- **MLflow** (porta 5001) - Tracking de experimentos
- **ThingsBoard** (porta 8081) - Dashboard de visualização
- **FastAPI** (porta 8001) - API de ingestão e predição

### Passo 3: Aguardar Inicialização

O ThingsBoard demora alguns minutos para inicializar na primeira vez. Verifique o status:

```bash
docker-compose logs -f thingsboard
```

Aguarde até ver mensagens indicando que o serviço está pronto.

### Passo 4: Verificar se Tudo Está Funcionando

Acesse os serviços:

| Serviço        | URL                        | Credenciais                          |
| -------------- | -------------------------- | ------------------------------------ |
| FastAPI (Docs) | http://localhost:8001/docs | -                                    |
| MinIO Console  | http://localhost:9101      | grupo_hubfolio / horse-lock-electric |
| MLflow         | http://localhost:5001      | -                                    |
| ThingsBoard    | http://localhost:8081      | tenant@thingsboard.org / tenant      |

Teste o health check da API:

```bash
curl http://localhost:8001/health
```

## Fluxo do Projeto

### 1. Ingestão de Dados

OBS.: Basta ingerir apenas uma vez, caso faça a ingestão novamente os dados vão ficar duplicados, por exemplo: deve ter originalmente 150 portfólios, ingerindo novamente -> fica em 300

O FastAPI recebe dados de portfólios e armazena no MinIO:

```bash
curl -X POST "http://localhost:8001/ingest/hubfolio" \
  -H "Content-Type: application/json"
```

### 2. ETL (MinIO → PostgreSQL)

Executa a transformação dos dados:

```bash
curl -X POST "http://localhost:8001/etl/run"
```

### 3. Treinamento do Modelo

Abra o notebook `notebooks/ML_HubFolio.ipynb` e execute todas as células.

O modelo será salvo em `fastapi/models/hubfolio_model.pkl`.

### 4. Fazer Predições

Envie dados de um portfólio para obter a predição:

```bash
curl -X POST "http://localhost:8001/predict" \
  -H "Content-Type: application/json" \
  -d '{
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

### 5. Visualização no ThingsBoard

Você não precisa criar nada manualmente no ThingsBoard: basta importar o dashboard já pronto.

1. Acesse http://localhost:8081
2. ThingsBoard → Entidades → Dispositivos → `+` → **Adicionar novo dispositivo**.
3. Nome: `HubFolio Predictions` (perfil: default). Criar.
4. Abra o dispositivo criado → aba **Credenciais** → copie o **Access Token**.
5. No `docker-compose.yml` (ou `.env`), defina `THINGSBOARD_DEVICE_TOKEN` com esse token e rode:
   ```bash
   docker-compose restart fastapi
   ```
6. Importe o dashboard (`trendz/hubfolio_analytics_dashboard.json`), abra em **Edit mode** → **Aliases** e selecione o dispositivo `HubFolio Predictions` criado. Salve.

Pronto: os widgets já vêm configurados; basta ter o alias apontando para o dispositivo que recebe a telemetria.

#### Testar com Dados de Streaming

```bash
python scripts/stream_simulator_local.py --limit 10 --delay 1
```

## Scripts Disponíveis

| Script                              | Descrição                      |
| ----------------------------------- | ------------------------------ |
| `scripts/stream_simulator_local.py` | Simula envio de dados para API |
| `scripts/send_batch_predictions.py` | Envia predições em lote        |

## Estrutura do Projeto

```
/
├── docker-compose.yml    # Orquestração dos containers
├── fastapi/              # API de ingestão e ML
│   ├── main.py          # Endpoints FastAPI
│   ├── models/          # Modelos treinados (.pkl)
│   └── requirements.txt # Dependências da API
├── mlflow/               # Configuração MLflow
├── postgres/             # Schema do banco de dados
├── notebooks/            # Notebooks de análise e treinamento
│   ├── ML_HubFolio.ipynb
│   └── requirements-notebook.txt
├── trendz/               # Dashboards exportados (ThingsBoard)
├── reports/              # Plots gerados pelo notebook
├── data/                 # Dados de exemplo
├── scripts/              # Scripts utilitários
├── README.md
└── LICENSE
```

## API Endpoints

| Método | Endpoint           | Descrição                      |
| ------ | ------------------ | ------------------------------ |
| GET    | `/health`          | Verifica status dos serviços   |
| POST   | `/ingest/hubfolio` | Ingere dados do HubFólio       |
| POST   | `/etl/run`         | Executa ETL MinIO → PostgreSQL |
| POST   | `/predict`         | Faz predição de qualidade      |
| GET    | `/model/info`      | Info do modelo carregado       |
| POST   | `/model/upload`    | Upload de novo modelo          |

## Métricas do Modelo

O modelo prevê o **Índice de Qualidade (IQ)** do portfólio baseado em:

- `projetos_min` - Quantidade de projetos
- `habilidades_min` - Quantidade de habilidades listadas
- `kw_contexto` - Palavras-chave de contexto
- `kw_processo` - Palavras-chave de processo
- `kw_resultado` - Palavras-chave de resultado
- `consistencia_visual_score` - Score de consistência visual
- `bio` - Se possui bio
- `contatos` - Se possui contatos

**Desempenho**: RMSE ~5.13 pontos de IQ (modelo Regressão Linear)

## Comandos Úteis

```bash
# Ver logs de um serviço
docker-compose logs -f fastapi

# Reiniciar serviço específico
docker-compose restart fastapi

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (limpa dados)
docker-compose down -v

# Reconstruir containers após mudanças
docker-compose up -d --build
```

## Troubleshooting

### ThingsBoard não inicia

O ThingsBoard precisa do banco `thingsboard` no PostgreSQL. Verifique:

```bash
docker-compose exec postgres psql -U hubfolio_user -c "\l"
```

### Erro 401 no ThingsBoard

O token do dispositivo está incorreto. Copie o token correto:

1. ThingsBoard → Dispositivos → HubFolio Predictions → Credenciais
2. Atualize `THINGSBOARD_DEVICE_TOKEN` no `docker-compose.yml`
3. Execute: `docker-compose restart fastapi`

### FastAPI não conecta ao MinIO/PostgreSQL

Aguarde os serviços iniciarem completamente:

```bash
docker-compose ps  # Verificar se todos estão "Up"
```
