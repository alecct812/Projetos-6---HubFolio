# ✅ Solução: Métricas Zeradas e Descrição Vazia

## ❓ Por que está zerado?

As métricas estão zeradas porque **não foram passadas** quando você fez o upload. O código usa `0.0` como padrão quando não recebe métricas.

---

## ✅ SOLUÇÃO: Fazer Upload Novamente

### **Valores Reais do Seu Modelo (do Notebook):**

Baseado no notebook `MachineLearnig_HubFólio.ipynb`, o modelo **Linear Regression** tem:

- **R² Score:** `0.869` (86.9% - muito bom!)
- **RMSE:** `5.13` (erro médio de 5.13 pontos)
- **MAE:** `4.38` (erro absoluto médio de 4.38 pontos)

---

## 🚀 Como Corrigir (3 Opções)

### **Opção 1: Via Script Atualizado** ⭐ (Mais Fácil)

O script já foi atualizado com os valores corretos:

```bash
./test_upload_model.sh
```

Isso criará a **versão 2** com métricas e descrição corretas!

### **Opção 2: Via Swagger UI**

1. Acesse: **http://localhost:8001/docs**
2. Encontre: `POST /model/upload`
3. Clique em: **"Try it out"**
4. Escolha o arquivo: `fastapi/models/hubfolio_model.pkl`
5. **Preencha as métricas:**
   - `r2_score`: `0.869`
   - `rmse`: `5.13`
   - `mae`: `4.38`
6. Clique em: **"Execute"**

### **Opção 3: Via Terminal (cURL)**

```bash
curl -X POST "http://localhost:8001/model/upload" \
  -F "file=@fastapi/models/hubfolio_model.pkl" \
  -F "r2_score=0.869" \
  -F "rmse=5.13" \
  -F "mae=4.38" \
  -F "model_name=hubfolio-model"
```

---

## 📊 O que Vai Acontecer?

Após fazer upload novamente:

1. ✅ **Nova versão criada** (versão 2)
2. ✅ **Métricas aparecem** no MLflow:
   - R² Score: 0.869
   - RMSE: 5.13
   - MAE: 4.38
3. ✅ **Descrição automática** será adicionada:
   - "R²: 0.869 | RMSE: 5.13 | MAE: 4.38"
4. ✅ **Versão 1** continua existindo (com valores zerados)
   - Você pode deletar depois se quiser

---

## 🔍 Verificar se Funcionou

### **1. No MLflow UI:**

1. Acesse: **http://localhost:5001**
2. Vá para **"Experiments"** → **"hubfolio-models"**
3. Você verá um **novo run** com métricas preenchidas:
   - r2_score: 0.869
   - rmse: 5.13
   - mae: 4.38
4. Vá para **"Models"** → **"hubfolio-model"**
5. Você verá a **versão 2** com:
   - Descrição: "R²: 0.869 | RMSE: 5.13 | MAE: 4.38"
   - Métricas corretas

### **2. Via API:**

```bash
curl http://localhost:8001/model/info
```

Você verá informações sobre ambas as versões.

---

## 🗑️ Deletar Versão Antiga (Opcional)

Se quiser deletar a versão 1 com métricas zeradas:

1. No MLflow UI: **"Models"** → **"hubfolio-model"** → **Versão 1**
2. Clique em **"Delete"** ou **"Archive"**

Ou deixe como está - não faz mal ter versões antigas para histórico.

---

## ✅ Resumo

**Problema:**
- Métricas zeradas porque não foram passadas no upload
- Descrição vazia

**Solução:**
- Fazer upload novamente **com métricas preenchidas**
- Valores corretos: R²=0.869, RMSE=5.13, MAE=4.38

**Resultado:**
- Nova versão (2) com métricas e descrição corretas

**Agora é só executar:**
```bash
./test_upload_model.sh
```

**Pronto!** 🚀

