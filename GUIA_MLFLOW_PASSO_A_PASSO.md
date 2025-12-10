# 📘 Guia Passo a Passo - MLflow e Models

## 🎯 Por que está vazio?

O MLflow está funcionando perfeitamente! Mas está vazio porque **ainda não foi feito upload de nenhum modelo**. 

O MLflow só mostra dados **depois** que você:
1. Faz upload de um modelo via API
2. Registra o modelo no MLflow

---

## 📍 Como Acessar a Aba "Models"

### No MLflow UI:

1. **No topo da página**, você verá duas abas:
   - **"Experiments"** (onde você está agora)
   - **"Models"** ← Clique aqui!

2. Ou use o menu lateral esquerdo e procure por **"Models"**

3. **URL direta**: http://localhost:5001/#/models

---

## 🚀 Passo a Passo Completo

### **PASSO 1: Verificar se você tem um modelo**

Você precisa do arquivo `hubfolio_model.pkl`. Verifique se existe:

```bash
# Verificar se o modelo existe
ls -lh fastapi/models/hubfolio_model.pkl
# ou
ls -lh fastapi/notebooks/models/hubfolio_model.pkl
```

**Se não tiver o modelo:**
- Você precisa treinar o modelo primeiro no Jupyter Notebook
- Ou usar um modelo já treinado

---

### **PASSO 2: Fazer Upload do Modelo**

#### **Opção A: Via Swagger UI (Mais Fácil)** ⭐

1. Acesse: **http://localhost:8001/docs**

2. Encontre o endpoint: **`POST /model/upload`**

3. Clique em **"Try it out"**

4. Clique em **"Choose File"** e selecione:
   - `fastapi/models/hubfolio_model.pkl` 
   - OU `fastapi/notebooks/models/hubfolio_model.pkl`

5. **Opcionalmente**, preencha os campos de métricas:
   - `r2_score`: Ex: `0.85`
   - `rmse`: Ex: `12.5`
   - `mae`: Ex: `9.2`
   - `model_name`: `hubfolio-model` (padrão)

6. Clique em **"Execute"**

7. **Resposta esperada:**
```json
{
  "message": "Modelo carregado com sucesso!",
  "model_path": "/app/models/hubfolio_model.pkl",
  "file_size": 755,
  "mlflow_registered": true,
  "mlflow_run_id": "abc123...",
  "mlflow_model_version": "1",
  "s3_exported": true,
  "s3_key": "models/hubfolio-model/v1/..."
}
```

#### **Opção B: Via cURL**

```bash
curl -X POST "http://localhost:8001/model/upload" \
  -F "file=@fastapi/models/hubfolio_model.pkl" \
  -F "r2_score=0.85" \
  -F "rmse=12.5" \
  -F "mae=9.2" \
  -F "model_name=hubfolio-model"
```

---

### **PASSO 3: Verificar no MLflow**

Após fazer o upload:

1. **Atualize a página do MLflow** (F5 ou Cmd+R)

2. **Na aba "Experiments"**:
   - Você verá um **run** novo
   - Com métricas (r2_score, rmse, mae)
   - Com parâmetros do modelo

3. **Na aba "Models"**:
   - Clique em **"Models"** no topo
   - Você verá: **"hubfolio-model"**
   - Com versão **"1"** no stage **"Production"**

---

## 📊 O que você verá no MLflow

### **Na Aba "Experiments":**

- **Runs**: Cada upload cria um "run"
- **Métricas**: r2_score, rmse, mae
- **Parâmetros**: Tipo do modelo, número de features
- **Tags**: Data de upload, fonte

### **Na Aba "Models":**

- **Modelo Registrado**: "hubfolio-model"
- **Versões**: v1, v2, v3... (cada upload cria nova versão)
- **Stages**: Production, Staging, Archived
- **Run ID**: Link para o run original

---

## 🔍 Verificar se Funcionou

### 1. Verificar via API:

```bash
curl http://localhost:8001/model/info
```

**Resposta esperada:**
```json
{
  "model_loaded": true,
  "model_name": "LinearRegression",
  "features": [...],
  "mlflow": {
    "name": "hubfolio-model",
    "latest_versions": [
      {
        "version": "1",
        "stage": "Production",
        "run_id": "...",
        "created_at": "2025-12-10T..."
      }
    ]
  }
}
```

### 2. Verificar no MLflow UI:

- **Experiments**: Deve ter pelo menos 1 run
- **Models**: Deve ter "hubfolio-model" com versão 1

---

## 🎯 Resumo Rápido

1. ✅ **MLflow está funcionando** (você já viu!)
2. ⏳ **Falta fazer upload do modelo**
3. 📤 **Use**: http://localhost:8001/docs → `POST /model/upload`
4. 👀 **Veja resultado**: http://localhost:5001 → Aba "Models"

---

## ❓ Problemas Comuns

### "Não tenho o arquivo .pkl"

**Solução:**
- Treine o modelo no Jupyter Notebook primeiro
- Ou use um modelo de exemplo

### "Upload deu erro"

**Verifique:**
```bash
# Ver logs
docker-compose logs fastapi

# Verificar se MLflow está conectado
curl http://localhost:8001/health
```

### "Não aparece nada no MLflow"

**Solução:**
1. Aguarde alguns segundos após o upload
2. Atualize a página (F5)
3. Verifique se `mlflow_registered: true` na resposta do upload

---

## 🎓 Próximos Passos

Depois que o modelo estiver no MLflow:

1. ✅ Fazer predições via API
2. ✅ Ver histórico de versões
3. ✅ Comparar diferentes modelos
4. ✅ Exportar modelos para S3

**Tudo pronto!** Agora é só fazer o upload do modelo! 🚀

