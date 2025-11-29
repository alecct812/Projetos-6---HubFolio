# 🧪 Guia Completo - Como Testar a Predição com o Modelo

## 📋 Pré-requisitos

Antes de testar a predição, você precisa:

1. ✅ **API rodando** - `docker-compose up -d` (ou FastAPI rodando localmente)
2. ✅ **PostgreSQL com dados** - Execute `/etl/run` se ainda não tiver dados
3. ✅ **Modelo treinado** - Arquivo `hubfolio_model.pkl` disponível

---

## 🚀 Passo a Passo para Testar

### **PASSO 1: Verificar se a API está rodando**

```powershell
Invoke-WebRequest -Uri http://localhost:8001/health -Method GET
```

**Resposta esperada:**

```json
{
  "status": "healthy",
  "minio_connected": true,
  "bucket_exists": true,
  "postgres_connected": true,
  "timestamp": "2025-01-15T10:00:00.000Z"
}
```

---

### **PASSO 2: Verificar se há usuários no banco**

```powershell
Invoke-WebRequest -Uri http://localhost:8001/postgres/summary -Method GET
```

**Se não houver dados, execute o ETL:**

```powershell
Invoke-WebRequest -Uri http://localhost:8001/etl/run -Method POST
```

---

### **PASSO 3: Fazer Upload do Modelo**

Você tem **3 opções** para fazer upload do modelo:

#### **Opção A: Via Swagger UI (Mais Fácil)** ⭐

1. Acesse: http://localhost:8001/docs
2. Encontre o endpoint `POST /model/upload`
3. Clique em "Try it out"
4. Clique em "Choose File" e selecione: `notebooks/models/hubfolio_model.pkl`
5. Clique em "Execute"

**Resposta esperada:**

```json
{
  "message": "Modelo carregado com sucesso!",
  "model_path": "/app/models/hubfolio_model.pkl",
  "file_size": 755
}
```

#### **Opção B: Via PowerShell**

```powershell
$modelPath = "notebooks\models\hubfolio_model.pkl"
$uri = "http://localhost:8001/model/upload"

$form = @{
    file = Get-Item -Path $modelPath
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

#### **Opção C: Via cURL (se tiver)**

```bash
curl -X POST "http://localhost:8001/model/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@notebooks/models/hubfolio_model.pkl"
```

---

### **PASSO 4: Verificar se o Modelo foi Carregado**

```powershell
Invoke-WebRequest -Uri http://localhost:8001/model/info -Method GET
```

**Resposta esperada:**

```json
{
  "model_loaded": true,
  "model_name": "LinearRegression",
  "features": [
    "projetos_min",
    "habilidades_min",
    "kw_contexto",
    "kw_processo",
    "kw_resultado",
    "consistencia_visual_score",
    "bio",
    "contatos"
  ],
  "num_features": 8
}
```

⚠️ **Se `model_loaded: false`**, você precisa fazer o upload primeiro (PASSO 3).

---

### **PASSO 5: Fazer uma Predição**

Você tem **3 opções** para testar a predição:

#### **Opção A: Via Swagger UI (Mais Fácil)** ⭐

1. Acesse: http://localhost:8001/docs
2. Encontre o endpoint `POST /predict`
3. Clique em "Try it out"
4. Cole o JSON abaixo no campo "Request body"
5. Clique em "Execute"

**JSON de exemplo:**

```json
{
  "user_id": 1,
  "projetos_min": 5,
  "habilidades_min": 15,
  "kw_contexto": 5,
  "kw_processo": 4,
  "kw_resultado": 5,
  "consistencia_visual_score": 90,
  "bio": true,
  "contatos": true
}
```

#### **Opção B: Via PowerShell (usando arquivo JSON)**

```powershell
$json = Get-Content -Path "test_predict.json" -Raw
$uri = "http://localhost:8001/predict"

Invoke-RestMethod -Uri $uri -Method Post -Body $json -ContentType "application/json"
```

#### **Opção C: Via PowerShell (JSON inline)**

```powershell
$body = @{
    user_id = 1
    projetos_min = 5
    habilidades_min = 15
    kw_contexto = 5
    kw_processo = 4
    kw_resultado = 5
    consistencia_visual_score = 90
    bio = $true
    contatos = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/predict" -Method Post -Body $body -ContentType "application/json"
```

---

### **PASSO 6: Verificar a Resposta**

**Resposta esperada (sucesso):**

```json
{
  "sucesso": true,
  "indice_qualidade": 87.45,
  "classificacao": "Excelente",
  "feedback": ["Seu portfólio está bem estruturado!"],
  "model_name": "LinearRegression",
  "predicted_at": "2025-01-15T10:30:00.000Z",
  "portfolio_id": 123,
  "prediction_id": 456
}
```

---

## 📝 Arquivos de Teste Disponíveis

Você tem **3 arquivos de teste** prontos para usar:

### 1. **test_predict.json** (Avançado)

```json
{
  "user_id": 1,
  "projetos_min": 5,
  "habilidades_min": 15,
  "kw_contexto": 5,
  "kw_processo": 4,
  "kw_resultado": 5,
  "consistencia_visual_score": 90,
  "bio": true,
  "contatos": true
}
```

**Resultado esperado:** IQ alto (80-100) - "Excelente"

### 2. **test_iniciante.json** (Iniciante)

```json
{
  "user_id": 1,
  "projetos_min": 0,
  "habilidades_min": 2,
  "kw_contexto": 0,
  "kw_processo": 0,
  "kw_resultado": 0,
  "consistencia_visual_score": 40,
  "bio": false,
  "contatos": false
}
```

**Resultado esperado:** IQ baixo (0-40) - "Precisa Melhorar"

### 3. **test_intermediario.json** (Intermediário)

```json
{
  "user_id": 1,
  "projetos_min": 2,
  "habilidades_min": 6,
  "kw_contexto": 2,
  "kw_processo": 2,
  "kw_resultado": 2,
  "consistencia_visual_score": 65,
  "bio": true,
  "contatos": true
}
```

**Resultado esperado:** IQ médio (40-80) - "Bom" ou "Regular"

---

---

## ⚠️ Erros Comuns e Soluções

### Erro 1: "Modelo de ML não está carregado"

**Causa:** Modelo não foi feito upload  
**Solução:** Execute o PASSO 3 (Upload do Modelo)

### Erro 2: "Usuário com ID X não encontrado"

**Causa:** O `user_id` não existe no banco  
**Solução:**

- Verifique usuários disponíveis: `GET /postgres/summary`
- Use um `user_id` que existe (ex: 1, 2, 3...)
- Ou execute o ETL: `POST /etl/run`

### Erro 3: "PostgreSQL não está disponível"

**Causa:** PostgreSQL não está rodando  
**Solução:**

```powershell
docker-compose up -d postgres
```

### Erro 4: "Campos obrigatórios faltando"

**Causa:** JSON incompleto  
**Solução:** Verifique se todos os campos estão presentes:

- `user_id`, `projetos_min`, `habilidades_min`, `kw_contexto`, `kw_processo`, `kw_resultado`, `consistencia_visual_score`, `bio`, `contatos`

---

## 🎯 Teste Rápido (1 minuto)

Se você só quer testar rapidamente:

```powershell
# 1. Upload do modelo (se necessário)
$form = @{ file = Get-Item -Path "notebooks\models\hubfolio_model.pkl" }
Invoke-RestMethod -Uri "http://localhost:8001/model/upload" -Method Post -Form $form

# 2. Fazer predição
$json = Get-Content -Path "test_predict.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8001/predict" -Method Post -Body $json -ContentType "application/json"
```

---

## 📊 Verificar Predições Salvas no Banco

Após fazer predições, você pode verificar no banco:

```powershell
# Ver sumário do banco (inclui predições)
Invoke-RestMethod -Uri "http://localhost:8001/postgres/summary" -Method GET
```
---

**Pronto! Agora você pode testar a predição com o modelo.** 🚀
