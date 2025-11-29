# 📋 Guia do Endpoint `/predict`

## 🎯 Objetivo

O endpoint `/predict` realiza a predição do **Índice de Qualidade (IQ)** de um portfólio usando Machine Learning e registra os dados no PostgreSQL.

## 📝 Campos Obrigatórios do JSON

### Estrutura Completa:

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

### Descrição dos Campos:

| Campo | Tipo | Obrigatório | Descrição | Valores Válidos |
|-------|------|-------------|-----------|-----------------|
| **user_id** | `integer` | ✅ **SIM** | ID do usuário no banco de dados | Deve existir na tabela `users` |
| **projetos_min** | `integer` | ✅ SIM | Número de projetos no portfólio | `>= 0` |
| **habilidades_min** | `integer` | ✅ SIM | Número de habilidades listadas | `>= 0` |
| **kw_contexto** | `integer` | ✅ SIM | Quantidade de palavras-chave de contexto | `>= 0` |
| **kw_processo** | `integer` | ✅ SIM | Quantidade de palavras-chave de processo | `>= 0` |
| **kw_resultado** | `integer` | ✅ SIM | Quantidade de palavras-chave de resultado | `>= 0` |
| **consistencia_visual_score** | `float` | ✅ SIM | Score de consistência visual | `0.0 - 100.0` |
| **bio** | `boolean` | ✅ SIM | Se o usuário preencheu a bio | `true` ou `false` |
| **contatos** | `boolean` | ✅ SIM | Se o usuário incluiu informações de contato | `true` ou `false` |

## ⚠️ Validações Realizadas

### 1. Validação de `user_id`
- ✅ O `user_id` **DEVE existir** na tabela `users` do PostgreSQL
- ❌ Se o `user_id` não existir, a requisição retorna erro **404** com a mensagem:
  ```
  "Usuário com ID {user_id} não encontrado no banco de dados. Por favor, verifique o user_id e tente novamente."
  ```

### 2. Validação de Campos
- ✅ Todos os campos são obrigatórios
- ✅ Validação de tipos (inteiros, floats, booleanos)
- ✅ Validação de ranges (scores entre 0-100)

## 🔄 Fluxo de Execução

Quando você faz uma requisição POST para `/predict`:

1. **Validação do Modelo**: Verifica se o modelo de ML está carregado
2. **Validação do PostgreSQL**: Verifica se o banco está disponível
3. **Validação do `user_id`**: Verifica se o usuário existe no banco
4. **Validação dos Dados**: Valida todos os campos do portfólio
5. **Predição**: Executa o modelo de ML para calcular o IQ
6. **Inserção no Banco**:
   - Insere registro na tabela `portfolios`
   - Calcula e insere métricas na tabela `portfolio_metrics`
   - Salva a predição na tabela `predictions`
7. **Resposta**: Retorna o resultado com IQ, classificação e feedback

## 📊 Resposta Esperada

### Sucesso (200 OK):

```json
{
  "sucesso": true,
  "indice_qualidade": 87.45,
  "classificacao": "Excelente",
  "feedback": [
    "Seu portfólio está bem estruturado!"
  ],
  "model_name": "LinearRegression",
  "predicted_at": "2025-01-15T10:30:00.000Z",
  "portfolio_id": 123,
  "prediction_id": 456
}
```

### Erro - Usuário Não Encontrado (404):

```json
{
  "detail": "Usuário com ID 999 não encontrado no banco de dados. Por favor, verifique o user_id e tente novamente."
}
```

### Erro - Modelo Não Carregado (503):

```json
{
  "detail": "Modelo de ML não está carregado. Use POST /model/upload primeiro."
}
```

## 🧪 Exemplos de Uso

### Via cURL (PowerShell):

```powershell
Invoke-WebRequest -Uri "http://localhost:8001/predict" -Method POST `
  -H "Content-Type: application/json" `
  -Body '{
    "user_id": 1,
    "projetos_min": 5,
    "habilidades_min": 15,
    "kw_contexto": 5,
    "kw_processo": 4,
    "kw_resultado": 5,
    "consistencia_visual_score": 90,
    "bio": true,
    "contatos": true
  }'
```

### Via Python (requests):

```python
import requests

url = "http://localhost:8001/predict"
data = {
    "user_id": 1,
    "projetos_min": 5,
    "habilidades_min": 15,
    "kw_contexto": 5,
    "kw_processo": 4,
    "kw_resultado": 5,
    "consistencia_visual_score": 90,
    "bio": True,
    "contatos": True
}

response = requests.post(url, json=data)
print(response.json())
```

### Via Swagger UI:

1. Acesse: http://localhost:8001/docs
2. Encontre o endpoint `POST /predict`
3. Clique em "Try it out"
4. Cole o JSON no campo "Request body"
5. Clique em "Execute"

## 📌 Tabelas Afetadas no PostgreSQL

Após uma predição bem-sucedida, os seguintes registros são criados:

1. **`portfolios`**: Registro do portfólio vinculado ao `user_id`
2. **`portfolio_metrics`**: Métricas calculadas (completude, clareza, IQ)
3. **`predictions`**: Resultado da predição do modelo ML

## ⚡ Importante

- **O `user_id` é obrigatório e deve existir no banco antes de fazer a predição**
- Se você não tiver usuários cadastrados, use o endpoint `/etl/run` para carregar dados do dataset
- Ou crie usuários manualmente na tabela `users` antes de usar `/predict`

