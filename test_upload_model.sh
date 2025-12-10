#!/bin/bash
# Script para fazer upload do modelo no MLflow

echo "🚀 Fazendo upload do modelo para MLflow..."
echo ""

# Verificar qual arquivo usar
if [ -f "fastapi/models/hubfolio_model.pkl" ]; then
    MODEL_FILE="fastapi/models/hubfolio_model.pkl"
elif [ -f "fastapi/notebooks/models/hubfolio_model.pkl" ]; then
    MODEL_FILE="fastapi/notebooks/models/hubfolio_model.pkl"
else
    echo "❌ Erro: Arquivo hubfolio_model.pkl não encontrado!"
    echo "   Procure em: fastapi/models/ ou fastapi/notebooks/models/"
    exit 1
fi

echo "📄 Usando arquivo: $MODEL_FILE"
echo ""

# Fazer upload
echo "📤 Enviando para API..."
echo "📊 Usando métricas do modelo Linear Regression:"
echo "   R² Score: 0.869"
echo "   RMSE: 5.13"
echo "   MAE: 4.38"
echo ""
RESPONSE=$(curl -s -X POST "http://localhost:8001/model/upload" \
  -F "file=@$MODEL_FILE" \
  -F "r2_score=0.869" \
  -F "rmse=5.13" \
  -F "mae=4.38" \
  -F "model_name=hubfolio-model")

echo "✅ Resposta:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
echo ""

# Verificar se foi registrado
if echo "$RESPONSE" | grep -q "mlflow_registered.*true"; then
    echo "🎉 Modelo registrado no MLflow com sucesso!"
    echo ""
    echo "📊 Próximos passos:"
    echo "   1. Acesse: http://localhost:5001"
    echo "   2. Clique na aba 'Models' no topo"
    echo "   3. Você verá 'hubfolio-model' com versão 1"
    echo ""
    echo "   Ou veja na aba 'Experiments' o novo run criado!"
else
    echo "⚠️  Verifique se o MLflow está rodando e tente novamente"
fi

