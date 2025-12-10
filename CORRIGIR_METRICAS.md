# 🔧 Como Corrigir Métricas Zeradas no MLflow

## ❓ Por que as Métricas Estão Zeradas?

As métricas estão zeradas porque **não foram passadas** quando você fez o upload do modelo. O código usa valores padrão `0.0` quando não recebe métricas.

---

## ✅ Solução: Fazer Upload Novamente com Métricas

### **Opção 1: Via Swagger UI (Recomendado)** ⭐

1. **Acesse:** http://localhost:8001/docs
2. **Encontre:** `POST /model/upload`
3. **Clique em:** "Try it out"
4. **Escolha o arquivo:** `fastapi/models/hubfolio_model.pkl`
5. **IMPORTANTE - Preencha as métricas:**
   - `r2_score`: `0.85` (ou o valor real do seu modelo)
   - `rmse`: `12.5` (ou o valor real)
   - `mae`: `9.2` (ou o valor real)
6. **Clique em:** "Execute"

**Isso criará uma NOVA versão (versão 2) com as métricas corretas!**

### **Opção 2: Via Terminal**

```bash
curl -X POST "http://localhost:8001/model/upload" \
  -F "file=@fastapi/models/hubfolio_model.pkl" \
  -F "r2_score=0.85" \
  -F "rmse=12.5" \
  -F "mae=9.2" \
  -F "model_name=hubfolio-model"
```

### **Opção 3: Usar o Script Atualizado**

O script `test_upload_model.sh` já tem valores de exemplo. Você pode editá-lo com seus valores reais:

```bash
# Editar o script
nano test_upload_model.sh

# Alterar as linhas:
#   -F "r2_score=0.85"    ← Coloque seu valor real
#   -F "rmse=12.5"        ← Coloque seu valor real
#   -F "mae=9.2"          ← Coloque seu valor real

# Executar
./test_upload_model.sh
```

---

## 📊 Onde Encontrar os Valores Reais das Métricas?

### **Se você treinou o modelo no Jupyter Notebook:**

1. Abra o notebook: `fastapi/notebooks/MachineLearnig_HubFólio.ipynb`
2. Procure pelas células que calculam:
   - `r2_score` ou `R²`
   - `rmse` ou `RMSE`
   - `mae` ou `MAE`
3. Use esses valores no upload

### **Exemplo de onde procurar:**

```python
# No notebook, você deve ter algo como:
r2_score = model.score(X_test, y_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)

print(f"R² Score: {r2_score}")
print(f"RMSE: {rmse}")
print(f"MAE: {mae}")
```

**Use esses valores no upload!**

---

## 🎯 O que Acontece Agora?

Após fazer upload com métricas:

1. ✅ **Nova versão criada** (versão 2)
2. ✅ **Métricas aparecem** no MLflow (não mais zeradas)
3. ✅ **Descrição automática** será adicionada com as métricas
4. ✅ **Versão 1** continua existindo (com valores zerados)
5. ✅ Você pode **deletar a versão 1** se quiser

---

## 🔍 Verificar se Funcionou

### **1. No MLflow UI:**

1. Acesse: http://localhost:5001
2. Vá para **"Experiments"** → **"hubfolio-models"**
3. Você verá um **novo run** com métricas preenchidas
4. Vá para **"Models"** → **"hubfolio-model"**
5. Você verá a **versão 2** com descrição e métricas

### **2. Via API:**

```bash
curl http://localhost:8001/model/info
```

Você verá informações sobre ambas as versões.

---

## 📝 Exemplo de Valores Típicos

Se você não souber os valores exatos, pode usar valores de exemplo baseados em modelos similares:

```bash
# Valores de exemplo (substitua pelos seus valores reais)
r2_score=0.75   # R² entre 0 e 1 (quanto maior, melhor)
rmse=15.0       # RMSE em unidades do target (quanto menor, melhor)
mae=12.0        # MAE em unidades do target (quanto menor, melhor)
```

**Valores típicos para modelos de regressão:**
- **R² Score:** 0.6 - 0.9 (bom), > 0.9 (excelente)
- **RMSE:** 10-20% do range do target
- **MAE:** 8-15% do range do target

---

## 🗑️ Deletar Versão Antiga (Opcional)

Se quiser deletar a versão 1 com métricas zeradas:

1. No MLflow UI: **"Models"** → **"hubfolio-model"** → **Versão 1**
2. Clique em **"Delete"** ou **"Archive"**

Ou deixe como está - não faz mal ter versões antigas.

---

## ✅ Resumo

1. **Problema:** Métricas zeradas porque não foram passadas no upload
2. **Solução:** Fazer upload novamente **com métricas preenchidas**
3. **Resultado:** Nova versão (2) com métricas e descrição corretas

**Agora é só fazer upload novamente com as métricas!** 🚀

