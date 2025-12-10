# 🎓 Como Funciona o Sistema Completo - Guia Passo a Passo

## 📋 Visão Geral

Este guia explica **passo a passo** como tudo funciona, desde subir os serviços até ver os dados no MLflow.

---

## 🚀 PARTE 1: Subir os Serviços

### **Passo 1: Subir tudo**

```bash
docker-compose up -d --build
```

**O que acontece:**
- ✅ Cria 4 containers: MinIO, PostgreSQL, MLflow, FastAPI
- ✅ Cria o bucket `mlflow-artifacts` automaticamente
- ✅ Conecta todos os serviços

**Tempo:** ~2-3 minutos na primeira vez

### **Passo 2: Verificar se está tudo rodando**

```bash
docker-compose ps
```

**Você deve ver:**
```
NAME                STATUS
hubfolio_minio      Up (healthy)
hubfolio_postgres   Up (healthy)
hubfolio_mlflow     Up
hubfolio_fastapi    Up
```

---

## 📤 PARTE 2: Fazer Upload do Modelo

### **Passo 1: Preparar o modelo**

Você precisa do arquivo `hubfolio_model.pkl`. Ele deve estar em:
- `fastapi/models/hubfolio_model.pkl` ✅ (já existe)
- OU `fastapi/notebooks/models/hubfolio_model.pkl` ✅ (já existe)

### **Passo 2: Fazer upload via API**

#### **Opção A: Via Navegador (Mais Fácil)** ⭐

1. **Acesse:** http://localhost:8001/docs
2. **Encontre:** `POST /model/upload`
3. **Clique em:** "Try it out"
4. **Clique em:** "Choose File"
5. **Selecione:** `fastapi/models/hubfolio_model.pkl`
6. **Preencha métricas (opcional):**
   - `r2_score`: `0.85`
   - `rmse`: `12.5`
   - `mae`: `9.2`
7. **Clique em:** "Execute"

#### **Opção B: Via Terminal**

```bash
./test_upload_model.sh
```

### **Passo 3: Ver a resposta**

**Resposta esperada:**
```json
{
  "message": "Modelo carregado com sucesso!",
  "mlflow_registered": true,
  "mlflow_run_id": "e74fbbb440914798a6e0f201a7c16807",
  "mlflow_model_version": "1",
  "s3_exported": true
}
```

**O que aconteceu:**
1. ✅ Modelo foi salvo no FastAPI
2. ✅ Modelo foi registrado no MLflow (criou um "run")
3. ✅ Versão 1 foi criada no Model Registry
4. ✅ Modelo foi exportado para S3 (MinIO)

---

## 👀 PARTE 3: Ver no MLflow

### **Passo 1: Acessar o MLflow**

Abra no navegador: **http://localhost:5001**

### **Passo 2: Ver os Dados**

#### **A) Na Aba "Experiments"**

1. **Clique em:** "Experiments" (no topo)
2. **Você verá:**
   - Experimento: **"hubfolio-models"**
   - Um **run** listado (com o Run ID)
3. **Clique no run** para ver:
   - ✅ **Metrics:** r2_score, rmse, mae
   - ✅ **Parameters:** model_type, features_count
   - ✅ **Artifacts:** Pasta `model/` com o modelo

#### **B) Na Aba "Models"**

1. **Clique em:** "Models" (no topo)
2. **Você verá:**
   - Modelo: **"hubfolio-model"**
   - Latest version: **1**
   - Stage: **Production**
3. **Clique em "hubfolio-model"**
4. **Clique na versão "1"**
5. **Você verá:**
   - Informações da versão
   - **Run ID:** e74fbbb440914798a6e0f201a7c16807
   - **Source:** Link para os artifacts

---

## 🔄 FLUXO COMPLETO (Resumo Visual)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SUBIR SERVIÇOS                                            │
│    docker-compose up -d --build                              │
│    ↓                                                          │
│    ✅ MinIO, PostgreSQL, MLflow, FastAPI rodando            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. FAZER UPLOAD DO MODELO                                    │
│    POST /model/upload (com arquivo .pkl)                     │
│    ↓                                                          │
│    ✅ Modelo salvo no FastAPI                                 │
│    ✅ Run criado no MLflow                                   │
│    ✅ Versão 1 registrada                                    │
│    ✅ Exportado para S3                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. VER NO MLFLOW                                             │
│    http://localhost:5001                                     │
│    ↓                                                          │
│    Aba "Experiments" → Ver run com métricas                  │
│    Aba "Models" → Ver modelo versão 1                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Onde Está Cada Coisa?

### **1. Modelo Original (.pkl)**
- **Local:** `fastapi/models/hubfolio_model.pkl`
- **No Container:** `/app/models/hubfolio_model.pkl`

### **2. Modelo no MLflow (Run)**
- **Experimento:** "hubfolio-models"
- **Run ID:** e74fbbb440914798a6e0f201a7c16807
- **Artifacts:** Pasta `model/` dentro do run

### **3. Modelo no Model Registry**
- **Nome:** "hubfolio-model"
- **Versão:** 1
- **Stage:** Production
- **Link para Run:** e74fbbb440914798a6e0f201a7c16807

### **4. Modelo no S3 (MinIO)**
- **Bucket:** `mlflow-artifacts`
- **Caminho:** `1/e74fbbb440914798a6e0f201a7c16807/artifacts/model/`
- **Arquivos:** model.pkl, MLmodel, conda.yaml, etc.

---

## 🎯 Comandos Rápidos

### **Verificar Status:**
```bash
docker-compose ps
curl http://localhost:8001/health
```

### **Fazer Upload:**
```bash
./test_upload_model.sh
```

### **Ver no MLflow:**
- Abra: http://localhost:5001
- Clique em "Experiments" ou "Models"

### **Ver Logs:**
```bash
docker-compose logs fastapi --tail 50
docker-compose logs mlflow --tail 50
```

---

## ❓ Perguntas Frequentes

### **"Onde está o modelo?"**
- **No MLflow:** Aba "Experiments" → Run → Artifacts → model/
- **No S3:** Bucket `mlflow-artifacts`
- **No FastAPI:** `/app/models/hubfolio_model.pkl`

### **"Por que a versão 1 parece vazia?"**
- A página da versão mostra **metadados** (versão, stage, run ID)
- Os **artifacts** estão no **run original**
- Clique no **Run ID** para ver os artifacts

### **"Como vejo as métricas?"**
- Aba "Experiments" → Clique no run → Veja "Metrics"
- Ou: Aba "Models" → Clique no modelo → Clique na versão → Clique no Run ID

### **"Como faço uma nova versão?"**
- Faça upload novamente com o mesmo `model_name`
- MLflow criará automaticamente a versão 2

---

## ✅ Checklist de Funcionamento

- [ ] Serviços rodando (`docker-compose ps`)
- [ ] Upload do modelo feito (`mlflow_registered: true`)
- [ ] Run visível na aba "Experiments"
- [ ] Modelo visível na aba "Models"
- [ ] Versão 1 criada
- [ ] Artifacts no S3

---

## 🎓 Resumo em 3 Passos

1. **Subir:** `docker-compose up -d --build`
2. **Upload:** `./test_upload_model.sh` ou via http://localhost:8001/docs
3. **Ver:** http://localhost:5001 → Aba "Experiments" ou "Models"

**Pronto!** Agora você entende como tudo funciona! 🚀

