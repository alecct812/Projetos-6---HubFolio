# 📘 Explicação: O que aparece na Versão 1 do Modelo no MLflow

## 🎯 É Normal Estar "Vazio"?

**Sim!** A página da versão do modelo no MLflow mostra principalmente **metadados** da versão, não os artifacts diretamente.

---

## 📊 O que você DEVE ver na Versão 1:

### **Na Página da Versão do Modelo:**

1. **Informações da Versão:**
   - Versão: 1
   - Stage: Production
   - Criado em: [data/hora]
   - Run ID: e74fbbb440914798a6e0f201a7c16807

2. **Link para o Run Original:**
   - Clique no **Run ID** para ver os artifacts
   - Ou clique em **"Source Run"**

3. **Ações Disponíveis:**
   - Transicionar para outro stage
   - Deletar versão
   - Adicionar descrição

---

## 🔍 Onde estão os Artifacts?

Os **artifacts** (modelo, métricas, parâmetros) estão no **Run Original**, não diretamente na página da versão.

### **Como Acessar os Artifacts:**

#### **Opção 1: Via Run ID (Recomendado)**

1. Na página da versão, clique no **Run ID** (e74fbbb440914798a6e0f201a7c16807)
2. Você será redirecionado para o **Run Original**
3. Lá você verá:
   - ✅ **Artifacts** → Pasta `model/` com:
     - `model.pkl` (o modelo)
     - `MLmodel` (metadados)
     - `conda.yaml` (ambiente)
     - `requirements.txt` (dependências)
   - ✅ **Metrics** → r2_score, rmse, mae
   - ✅ **Parameters** → model_type, features_count
   - ✅ **Tags** → uploaded_at, source, model_type

#### **Opção 2: Via Aba "Experiments"**

1. Vá para a aba **"Experiments"**
2. Clique no experimento **"hubfolio-models"**
3. Você verá o run listado
4. Clique no run para ver todos os artifacts

---

## 📁 Estrutura dos Artifacts

Os artifacts foram salvos corretamente no S3 (MinIO):

```
mlflow-artifacts/
└── 1/
    └── e74fbbb440914798a6e0f201a7c16807/
        └── artifacts/
            └── model/
                ├── model.pkl          ← O modelo treinado
                ├── MLmodel            ← Metadados do MLflow
                ├── conda.yaml         ← Ambiente conda
                ├── requirements.txt   ← Dependências Python
                └── python_env.yaml    ← Ambiente Python
```

---

## ✅ Verificação Rápida

### **1. Verificar se os Artifacts Existem:**

```bash
docker-compose exec minio mc ls myminio/mlflow-artifacts/ --recursive
```

Você deve ver os arquivos listados acima.

### **2. Verificar no MLflow UI:**

1. Acesse: http://localhost:5001
2. Vá para **"Experiments"** → **"hubfolio-models"**
3. Clique no **run** (deve ter um run com as métricas)
4. Você verá a pasta **"model"** com todos os artifacts

### **3. Verificar Informações da Versão:**

```bash
curl http://localhost:8001/model/info
```

---

## 🎯 Resumo

- ✅ **Versão 1 foi criada corretamente**
- ✅ **Artifacts foram salvos no S3**
- ✅ **Run foi criado com métricas e parâmetros**
- ℹ️ **A página da versão mostra metadados, não artifacts diretamente**
- 🔗 **Clique no Run ID para ver os artifacts**

---

## 💡 Dica

Se você quiser ver os artifacts diretamente na página da versão, você pode:

1. **Adicionar uma descrição** na versão explicando o modelo
2. **Usar tags** para adicionar mais informações
3. **Clicar no Run ID** para ver todos os detalhes

---

## 🔍 O que você DEVE ver:

### **Na Aba "Models":**
- Modelo: **hubfolio-model**
- Latest version: **1**
- Stage: **Production**

### **Ao Clicar na Versão 1:**
- Informações da versão
- Link para o Run ID
- Opções de gerenciamento

### **Ao Clicar no Run ID:**
- ✅ Artifacts (pasta model/)
- ✅ Metrics (r2_score, rmse, mae)
- ✅ Parameters (model_type, features_count)
- ✅ Tags (uploaded_at, source)

**Tudo está funcionando corretamente!** 🎉

