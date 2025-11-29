# 📘 Guia: Exportação de Modelo Machine Learning

## O que é Exportação de Modelo?

A **exportação de modelo** é o processo de salvar um modelo treinado em um arquivo para uso posterior, sem precisar retreiná-lo. Isso permite:

- ✅ Reutilizar o modelo em produção (APIs, apps)
- ✅ Compartilhar modelos com outras pessoas/sistemas
- ✅ Versionar modelos (controle de qualidade)
- ✅ Reduzir tempo de inicialização (não precisa treinar sempre)

---

## 🔧 Métodos de Exportação em Python

### 1. **Pickle** (Método Padrão Python)

```python
import pickle

# Salvar modelo
with open('modelo.pkl', 'wb') as f:
    pickle.dump(modelo_treinado, f)

# Carregar modelo
with open('modelo.pkl', 'rb') as f:
    modelo_carregado = pickle.load(f)
```

**Prós:**

- Nativo do Python (biblioteca padrão)
- Funciona com qualquer objeto Python
- Simples de usar

**Contras:**

- Não é seguro (pode executar código malicioso)
- Não é compatível entre versões Python diferentes
- Não funciona em outras linguagens

---

### 2. **Joblib** (Otimizado para NumPy/scikit-learn)

```python
import joblib

# Salvar modelo
joblib.dump(modelo_treinado, 'modelo.joblib')

# Carregar modelo
modelo_carregado = joblib.load('modelo.joblib')
```

**Prós:**

- Mais eficiente que pickle para arrays NumPy grandes
- Recomendado pela documentação do scikit-learn
- Compressão automática

**Contras:**

- Mesmas limitações de segurança do pickle

---

### 3. **ONNX** (Formato Universal)

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

# Definir tipo de entrada
initial_type = [('float_input', FloatTensorType([None, 8]))]

# Converter para ONNX
onnx_model = convert_sklearn(modelo_treinado, initial_types=initial_type)

# Salvar
with open('modelo.onnx', 'wb') as f:
    f.write(onnx_model.SerializeToString())
```

**Prós:**

- Formato universal (funciona em C++, Java, JavaScript, etc.)
- Otimizado para produção
- Suporte a hardware especializado (GPU, TPU)

**Contras:**

- Mais complexo
- Nem todos os modelos são suportados

---

## 🎯 Processo Completo no HubFólio

### Passo 1: Treinar Modelo no Notebook

```python
from sklearn.linear_model import LinearRegression

# Treinar modelo
model = LinearRegression()
model.fit(X_train, y_train)

# Avaliar
score = model.score(X_test, y_test)
print(f"R² Score: {score:.4f}")
```

### Passo 2: Exportar como .pkl

```python
import pickle
import os

# Criar diretório para modelos
os.makedirs('models', exist_ok=True)

# Salvar modelo
model_path = 'models/hubfolio_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f"✅ Modelo salvo em: {model_path}")
print(f"   Tamanho: {os.path.getsize(model_path)} bytes")
```

### Passo 3: Testar Carregamento

```python
# Carregar modelo do disco
with open(model_path, 'rb') as f:
    modelo_carregado = pickle.load(f)

# Testar predição
exemplo = [[3, 10, 4, 3, 4, 80, 1, 1]]  # valores de exemplo
predicao = modelo_carregado.predict(exemplo)
print(f"Predição: {predicao[0]:.2f}")
```

### Passo 4: Upload para API FastAPI

**Opção A - Via curl/PowerShell:**

```powershell
# PowerShell
$headers = @{
    "Content-Type" = "multipart/form-data"
}
Invoke-WebRequest -Uri http://localhost:8001/model/upload `
    -Method POST `
    -InFile "models\hubfolio_model.pkl"
```

**Opção B - Via Swagger UI:**

1. Acesse http://localhost:8001/docs
2. Encontre o endpoint `POST /model/upload`
3. Clique em "Try it out"
4. Faça upload do arquivo `hubfolio_model.pkl`
5. Execute

**Opção C - Via Python (requests):**

```python
import requests

url = "http://localhost:8001/model/upload"
files = {'file': open('models/hubfolio_model.pkl', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

---

## 🧪 Validação Pós-Upload

### Verificar se modelo foi carregado:

```powershell
Invoke-WebRequest -Uri http://localhost:8001/model/info
```

**Resposta esperada:**

```json
{
  "model_loaded": true,
  "model_type": "LinearRegression",
  "model_path": "/app/models/hubfolio_model.pkl",
  "features_expected": 8
}
```

### Testar predição:

```powershell
$body = @{
    projetos_min = 3
    habilidades_min = 10
    kw_contexto = 4
    kw_processo = 3
    kw_resultado = 4
    consistencia_visual_score = 80
    bio = 1
    contatos = 1
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8001/predict `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

---

## 📋 Checklist Completo

- [ ] Ambiente virtual criado (`python -m venv venv`)
- [ ] Dependências instaladas (`pip install -r requirements-notebook.txt`)
- [ ] Notebook aberto no Jupyter
- [ ] Dados carregados (150 registros)
- [ ] Modelos treinados (Linear Regression, Decision Tree, KNN)
- [ ] Melhor modelo selecionado
- [ ] Modelo exportado como `.pkl`
- [ ] Teste de carregamento executado
- [ ] Modelo enviado para API
- [ ] Endpoint `/model/info` retorna sucesso
- [ ] Predição teste executada com sucesso

---

## ⚠️ Boas Práticas

### 1. **Salvar Metadados Junto com o Modelo**

```python
import pickle

modelo_completo = {
    'model': modelo_treinado,
    'features': ['projetos_min', 'habilidades_min', ...],
    'metrics': {
        'r2_score': 0.85,
        'rmse': 12.5,
        'mae': 9.2
    },
    'training_date': '2025-11-25',
    'training_samples': 150
}

with open('models/hubfolio_model_v1.pkl', 'wb') as f:
    pickle.dump(modelo_completo, f)
```

### 2. **Versionamento**

```
models/
├── hubfolio_model_v1.0.pkl  # Baseline (Linear Regression)
├── hubfolio_model_v1.1.pkl  # Decision Tree
├── hubfolio_model_v2.0.pkl  # Ensemble
└── production/
    └── hubfolio_model.pkl    # Modelo em produção
```

### 3. **Validação Pré-Deploy**

```python
# Antes de fazer upload, valide o modelo
def validar_modelo(modelo, X_test, y_test):
    """Valida modelo antes de deploy"""

    # 1. Verificar tipo
    assert hasattr(modelo, 'predict'), "Modelo não tem método predict()"

    # 2. Testar predição
    y_pred = modelo.predict(X_test)
    assert len(y_pred) == len(y_test), "Tamanho de predição incorreto"

    # 3. Verificar range
    assert y_pred.min() >= 0 and y_pred.max() <= 100, "IQ fora do range 0-100"

    print("✅ Modelo validado com sucesso!")
    return True

validar_modelo(modelo_final, X_test, y_test)
```

---

## 🎓 Resumo

**Pickle vs Joblib:**

- Use **Pickle** para modelos pequenos e simples
- Use **Joblib** para modelos grandes com arrays NumPy

**Para o HubFólio:**

- Modelo LinearRegression é pequeno → **Pickle é suficiente**
- 8 features, 150 amostras → Arquivo ~5-20 KB

**Fluxo Recomendado:**

1. Treinar no Jupyter Notebook
2. Exportar com Pickle
3. Testar localmente
4. Upload via Swagger UI
5. Validar via `/model/info`
6. Testar predição
