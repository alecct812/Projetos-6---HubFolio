# 🎓 HubFólio - Sistema de Avaliação de Qualidade de Portfólios

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📚 Informações Acadêmicas

**Disciplina:** Aprendizado de Máquina - 2025.2  
**Instituição:** CESAR School

> **💡 IMPORTANTE:** Os dados **persistem** entre reinicializações graças aos volumes do Docker. Você só precisa carregar os dados (ingest + ETL) **uma única vez** na primeira execução. Nas próximas vezes, basta `docker-compose up -d` e os dados estarão lá!

---

## 📋 Sobre o Projeto

O **HubFólio** é uma plataforma que utiliza Machine Learning para avaliar a qualidade de portfólios de estudantes de Design e Ciência da Computação, fornecendo:

- ✅ **Índice de Qualidade (IQ)** - Score de 0-100 baseado em múltiplos critérios
- 📊 **Métricas Detalhadas** - Completude, Clareza e Consistência Visual
- 💡 **Feedback Personalizado** - Sugestões específicas de melhoria
- 🤖 **Predição em Tempo Real** - API REST para integração

### Pipeline Completo

```
┌─────────────┐    ┌─────────┐    ┌──────────────┐    ┌─────────┐
│   FastAPI   │───▶│  MinIO  │───▶│  PostgreSQL  │───▶│ Jupyter │
│  (Ingestão) │    │  (S3)   │    │ (Estrutura)  │    │(Análise)│
└─────────────┘    └─────────┘    └──────────────┘    └─────────┘
                                                             │
                                           ┌─────────────────┘
                                           │ Modelo Treinado
                                           ▼
                                    ┌──────────────┐
                                    │  FastAPI ML  │
                                    │  (Inferência)│
                                    └──────────────┘
```

---

## 🚀 Quick Start

### Pré-requisitos

- **Docker Desktop** (versão 20.10+)
- **Docker Compose** (versão 2.0+)
- **Git**

### 🆕 Primeira Vez (Setup Inicial)

#### Passo 1: Clonar o Repositório

```powershell
git clone <seu-repositorio>
cd hubfolio
```

#### Passo 2: Levantar a Infraestrutura

```powershell
docker-compose up -d
```

**Saída esperada:**

```
[+] Running 3/3
 ✔ Container hubfolio_minio      Started
 ✔ Container hubfolio_postgres   Started
 ✔ Container hubfolio_fastapi    Started
```

#### Passo 3: Carregar Dados no MinIO (APENAS NA PRIMEIRA VEZ)

```powershell
Invoke-WebRequest -Uri http://localhost:8001/ingest/hubfolio -Method POST
```

**Ou acesse:** http://localhost:8001/docs e teste o endpoint `POST /ingest/hubfolio`

#### Passo 4: Executar ETL (MinIO → PostgreSQL) (APENAS NA PRIMEIRA VEZ)

```powershell
Invoke-WebRequest -Uri http://localhost:8001/etl/run -Method POST
```

#### Passo 5: Verificar Dados

```powershell
Invoke-WebRequest -Uri http://localhost:8001/postgres/summary -Method GET
```

**Resposta esperada:**

```json
{
  "tables": {
    "users": 150,
    "portfolios": 150,
    "portfolio_metrics": 150,
    "predictions": 0
  }
}
```

✅ **Pronto!** Os dados agora estão persistidos nos volumes do Docker.

---

### 🔄 Próximas Vezes (Reinicializações)

Quando você parar e subir os containers novamente, os dados **permanecem** (não precisa recarregar):

```powershell
# Parar containers
docker-compose down

# Subir novamente (dados permanecem nos volumes)
docker-compose up -d

# ✅ Dados já estão lá! Não precisa fazer ingest/ETL novamente
```

**Verificar que os dados continuam:**

```powershell
Invoke-WebRequest -Uri http://localhost:8001/postgres/summary -Method GET
```

---

### 🗑️ Reset Completo (Começar do Zero)

Se quiser apagar TUDO e recomeçar:

```powershell
# Para e remove containers + volumes (apaga dados)
docker-compose down -v

# Subir do zero
docker-compose up -d

# Recarregar dados (primeira vez de novo)
Invoke-WebRequest -Uri http://localhost:8001/ingest/hubfolio -Method POST
Invoke-WebRequest -Uri http://localhost:8001/etl/run -Method POST
```

---

## 🔗 Acessos aos Serviços

| Serviço               | URL                        | Credenciais                                                                   |
| --------------------- | -------------------------- | ----------------------------------------------------------------------------- |
| **FastAPI (Swagger)** | http://localhost:8000/docs | -                                                                             |
| **MinIO Console**     | http://localhost:9001      | User: `hubfolio_admin`<br>Password: `hubfolio_secret_2025`                    |
| **PostgreSQL**        | `localhost:5432`           | User: `hubfolio_user`<br>Password: `hubfolio_password_2025`<br>DB: `hubfolio` |

---

## 📊 Dataset

- **Fonte:** Dados mockados de 150 portfólios de estudantes
- **Arquivo:** `data/hubfolio_mock_data.json`
- **Registros:** 150 usuários
- **Features:**
  - Seções preenchidas (bio, projetos, habilidades, contatos)
  - Palavras-chave de clareza (contexto, processo, resultado)
  - Score de consistência visual (0-100)

---

## 🧪 Testando a API

### 1. Via Swagger UI (Recomendado)

Acesse: http://localhost:8001/docs

### 2. Via cURL - Health Check

```powershell
Invoke-WebRequest -Uri http://localhost:8001/health
```

### 3. Fazer uma Predição (após treinar o modelo)

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/predict" -Method POST `
  -H "Content-Type: application/json" `
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

**Resposta esperada:**

```json
{
  "sucesso": true,
  "indice_qualidade": 78.5,
  "classificacao": "Bom",
  "feedback": ["Seu portfólio está bem estruturado!"],
  "model_name": "LinearRegression",
  "predicted_at": "2025-11-25T10:30:00.000Z"
}
```

---

## 📁 Estrutura do Projeto

```
hubfolio/
├── docker-compose.yml          # Orquestração dos contêineres
├── README.md                   # Este arquivo
│
├── data/                       # Dataset
│   └── hubfolio_mock_data.json # 150 portfólios mockados
│
├── fastapi/                    # Camada de ingestão e ML
│   ├── Dockerfile
│   ├── main.py                 # Aplicação FastAPI
│   ├── minio_client.py         # Cliente MinIO/S3
│   ├── postgres_client.py      # Cliente PostgreSQL
│   ├── etl_minio_postgres.py   # ETL MinIO → PostgreSQL
│   ├── load_data.py            # Script de carga inicial
│   └── requirements.txt
│
├── postgres/                   # Configuração do banco
│   └── init.sql                # Schema e estrutura de tabelas
│
├── notebooks/                  # Análise e modelagem
│   └── (copie seu notebook aqui)
│
└── models/                     # Modelos treinados
    └── hubfolio_model.pkl      # Modelo exportado do notebook
```

**Volumes Docker (persistência de dados):**

```
Volumes criados automaticamente:
├── hubfolio_minio_data         # Arquivos do MinIO
└── hubfolio_postgres_data      # Banco de dados PostgreSQL
```

---

## 📈 Fluxo de Dados Completo

### 1️⃣ Ingestão (IMPLEMENTADO ✅)

```
Dataset Local → FastAPI → MinIO
```

- Lê `hubfolio_mock_data.json`
- Valida JSON
- Upload para MinIO (`hubfolio-data` bucket)

### 2️⃣ Estruturação (IMPLEMENTADO ✅)

```
MinIO → ETL Script → PostgreSQL
```

Tabelas criadas:

- `users` - Informações dos usuários
- `portfolios` - Dados brutos dos portfólios
- `portfolio_metrics` - Métricas calculadas (Completude, Clareza, IQ)
- `predictions` - Predições do modelo ML

### 3️⃣ Modelagem (PRÓXIMO PASSO)

```
PostgreSQL → Jupyter Notebook → Modelo Treinado → PostgreSQL
```

1. Carregar dados do PostgreSQL
2. Análise exploratória (EDA)
3. Treinar modelos (Linear Regression, Decision Tree, KNN)
4. Avaliar performance
5. Exportar melhor modelo como `.pkl`
6. Salvar predições no banco

### 4️⃣ Inferência (IMPLEMENTADO ✅)

```
API Request → FastAPI → Modelo ML → Resposta JSON
```

---

## 🤖 Machine Learning

### Modelos Implementados

1. **Linear Regression** (Baseline)
2. **Decision Tree Regressor**
3. **K-Nearest Neighbors (KNN)**

### Métricas Avaliadas

- **RMSE** (Root Mean Squared Error)
- **MAE** (Mean Absolute Error)
- **R² Score** (Coefficient of Determination)

### Features Utilizadas

```python
features = [
    'projetos_min',              # Número de projetos
    'habilidades_min',           # Número de habilidades
    'kw_contexto',               # Palavras-chave de contexto
    'kw_processo',               # Palavras-chave de processo
    'kw_resultado',              # Palavras-chave de resultado
    'consistencia_visual_score', # Score visual (0-100)
    'bio',                       # Tem bio? (0/1)
    'contatos'                   # Tem contatos? (0/1)
]
```

### Target (Variável Alvo)

```python
# Índice de Qualidade (IQ) = 0-100
IQ = (Completude × 0.4) + (Clareza × 0.4) + (Visual × 0.2)
```

---

## 📊 Endpoints da API

### MinIO (Data Ingestion)

- `POST /ingest/hubfolio` - Carrega dataset no MinIO
- `POST /upload` - Upload manual de arquivo
- `GET /files` - Lista arquivos no bucket

### PostgreSQL

- `GET /postgres/health` - Saúde do banco
- `GET /postgres/summary` - Sumário completo
- `GET /postgres/top-portfolios` - Top portfólios por IQ

### ETL

- `POST /etl/run` - Executa ETL completo (MinIO → PostgreSQL)

### Machine Learning

- `POST /predict` - Prediz IQ de um portfólio
- `GET /model/info` - Informações do modelo carregado
- `POST /model/upload` - Upload de modelo treinado (.pkl)

---

## 🔧 Desenvolvimento

### Logs dos Containers

```powershell
# Ver logs da API
docker-compose logs -f fastapi

# Ver logs do PostgreSQL
docker-compose logs -f postgres

# Ver logs do MinIO
docker-compose logs -f minio
```

### Acessar Container

```powershell
# Acessar FastAPI
docker exec -it hubfolio_fastapi /bin/bash

# Acessar PostgreSQL
docker exec -it hubfolio_postgres psql -U hubfolio_user -d hubfolio
```

### Reiniciar Serviços

```powershell
# Reiniciar tudo
docker-compose restart

# Reiniciar apenas FastAPI
docker-compose restart fastapi
```

---

## 🐛 Troubleshooting

### Erro: Containers não iniciam

```powershell
# Ver logs de erro
docker-compose logs

# Recriar containers
docker-compose down
docker-compose up -d --build
```

### Erro: MinIO não conecta

```powershell
# Verificar status
docker-compose ps minio

# Acessar console
# URL: http://localhost:9101
```

### Erro: Postgres não conecta

```powershell
# Verificar se está rodando
docker-compose ps postgres

# Testar conexão
docker exec -it hubfolio_postgres pg_isready -U hubfolio_user
```

---

## 📝 Referência Rápida

### Comandos Mais Usados

| Situação                                | Comando                                                          |
| --------------------------------------- | ---------------------------------------------------------------- |
| **Primeira vez (setup)**                | `docker-compose up -d` → Ingest → ETL                            |
| **Parar containers**                    | `docker-compose down`                                            |
| **Subir containers (dados permanecem)** | `docker-compose up -d`                                           |
| **Ver logs da API**                     | `docker-compose logs -f fastapi`                                 |
| **Reset completo (apaga dados)**        | `docker-compose down -v` → `docker-compose up -d` → Ingest → ETL |
| **Verificar dados**                     | `GET /postgres/summary`                                          |
| **Reiniciar apenas API**                | `docker-compose restart fastapi`                                 |

### Persistência de Dados

✅ **Dados persistem** nos volumes Docker:

- `hubfolio_minio_data` - Arquivos do MinIO
- `hubfolio_postgres_data` - Banco PostgreSQL

✅ **Você SÓ precisa** carregar dados (ingest + ETL) na **primeira vez**

✅ **Nas próximas vezes**, apenas `docker-compose up -d` (dados já estão lá)

❌ **Para apagar tudo**, use `docker-compose down -v` (remove volumes)

---

## 📝 Próximos Passos

- [✅] **Treinar modelo** com 150 dados no Jupyter Notebook
- [ ] **Exportar modelo** como `hubfolio_model.pkl`
- [ ] **Upload do modelo** via `POST /model/upload`
- [ ] **Testar predições** via `POST /predict`
- [ ] **Integrar com frontend** (opcional)
- [ ] **Deploy em produção** (opcional)

---

## 📄 Licença

Este projeto está sob a licença MIT.
