"""
FastAPI - Sistema de Ingestão e Predição HubFólio
API para gerenciamento de dados e inferência do modelo de ML
"""
import os
import json
import pickle
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np

from minio_client import MinIOClient
from postgres_client import PostgreSQLClient
from etl_minio_postgres import HubFolioETL

# Inicializar FastAPI
app = FastAPI(
    title="HubFólio Data & ML API",
    description="API para ingestão de dados e predição de Índice de Qualidade de Portfólios",
    version="1.0.0"
)

# Inicializar clientes
minio_client = MinIOClient()
pg_client = None  # Será inicializado no startup


# ====================================================================
# MODELOS PYDANTIC
# ====================================================================

class HealthResponse(BaseModel):
    status: str
    minio_connected: bool
    bucket_exists: bool
    postgres_connected: bool
    timestamp: str


class FileInfo(BaseModel):
    filename: str
    size: int
    last_modified: str
    content_type: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    size: int
    bucket: str
    object_key: str


class PortfolioInput(BaseModel):
    user_id: int  # OBRIGATÓRIO: ID do usuário que deve existir no banco
    projetos_min: int
    habilidades_min: int
    kw_contexto: int
    kw_processo: int
    kw_resultado: int
    consistencia_visual_score: float
    bio: bool
    contatos: bool


class PredictionResponse(BaseModel):
    sucesso: bool
    indice_qualidade: float
    classificacao: str
    feedback: List[str]
    model_name: str
    predicted_at: str
    portfolio_id: Optional[int] = None
    prediction_id: Optional[int] = None


# ====================================================================
# CLASSE DE INFERÊNCIA DO MODELO
# ====================================================================

class HubFolioPredictor:
    """Classe para realizar inferências do Índice de Qualidade"""
    
    def __init__(self, modelo=None):
        self.modelo = modelo
        self.features = [
            'projetos_min', 'habilidades_min',
            'kw_contexto', 'kw_processo', 'kw_resultado',
            'consistencia_visual_score',
            'bio', 'contatos'
        ]
        self.model_name = "LinearRegression"  # Padrão
    
    def load_model(self, model_path: str):
        """Carrega modelo salvo do disco"""
        try:
            with open(model_path, 'rb') as f:
                self.modelo = pickle.load(f)
            print(f"✅ Modelo carregado: {model_path}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            return False
    
    def validar_entrada(self, dados: dict):
        """Valida se todos os campos obrigatórios estão presentes"""
        campos_faltantes = [f for f in self.features if f not in dados]
        if campos_faltantes:
            return False, f"Campos obrigatórios faltando: {campos_faltantes}"
        return True, "OK"
    
    def preprocessar(self, dados: dict):
        """Converte dados de entrada para formato do modelo"""
        # Converter booleanos para int
        if isinstance(dados.get('bio'), bool):
            dados['bio'] = int(dados['bio'])
        if isinstance(dados.get('contatos'), bool):
            dados['contatos'] = int(dados['contatos'])
        
        # Criar DataFrame com as features na ordem correta
        df_input = pd.DataFrame([dados])[self.features].astype(float)
        return df_input
    
    def prever(self, dados_portfolio: dict):
        """Realiza a predição do Índice de Qualidade"""
        # Validar entrada
        valido, mensagem = self.validar_entrada(dados_portfolio)
        if not valido:
            return {"erro": mensagem, "sucesso": False}
        
        # Preprocessar e prever
        X_input = self.preprocessar(dados_portfolio)
        iq_previsto = self.modelo.predict(X_input)[0]
        
        # Limitar entre 0 e 100
        iq_previsto = max(0, min(100, iq_previsto))
        
        # Gerar feedback baseado no score
        feedback = self._gerar_feedback(iq_previsto, dados_portfolio)
        
        return {
            "sucesso": True,
            "indice_qualidade": round(float(iq_previsto), 2),
            "classificacao": self._classificar_iq(iq_previsto),
            "feedback": feedback,
            "model_name": self.model_name,
            "predicted_at": datetime.utcnow().isoformat()
        }
    
    def _classificar_iq(self, iq: float) -> str:
        """Classifica o IQ em categorias"""
        if iq >= 80:
            return "Excelente"
        elif iq >= 60:
            return "Bom"
        elif iq >= 40:
            return "Regular"
        else:
            return "Precisa Melhorar"
    
    def _gerar_feedback(self, iq: float, dados: dict) -> List[str]:
        """Gera feedback personalizado baseado nos dados"""
        sugestoes = []
        
        if dados.get('projetos_min', 0) < 3:
            sugestoes.append("Adicione mais projetos ao seu portfólio (mínimo 3 recomendado)")
        if dados.get('habilidades_min', 0) < 5:
            sugestoes.append("Liste mais habilidades técnicas (mínimo 5)")
        if not dados.get('bio'):
            sugestoes.append("Adicione uma bio/sobre você")
        if not dados.get('contatos'):
            sugestoes.append("Inclua informações de contato")
        if (dados.get('kw_contexto', 0) + dados.get('kw_processo', 0) + dados.get('kw_resultado', 0)) < 9:
            sugestoes.append("Melhore a narrativa dos projetos (contexto, processo, resultado)")
        if dados.get('consistencia_visual_score', 0) < 70:
            sugestoes.append("Trabalhe na consistência visual do portfólio")
        
        return sugestoes if sugestoes else ["Seu portfólio está bem estruturado!"]


# Instância global do preditor
predictor = HubFolioPredictor()


# ====================================================================
# EVENTOS DE STARTUP/SHUTDOWN
# ====================================================================

@app.on_event("startup")
async def startup_event():
    """Inicializa recursos na inicialização da aplicação"""
    global pg_client, predictor
    
    # MinIO
    minio_client.create_bucket_if_not_exists()
    print(f"✅ Bucket '{minio_client.bucket_name}' verificado/criado com sucesso!")
    
    # PostgreSQL
    try:
        pg_client = PostgreSQLClient()
        if pg_client.check_connection():
            print(f"✅ PostgreSQL conectado com sucesso!")
        else:
            print(f"⚠️ PostgreSQL não está acessível")
    except Exception as e:
        print(f"⚠️ Erro ao conectar PostgreSQL: {e}")
        pg_client = None
    
    # Tentar carregar modelo
    model_path = "/app/models/hubfolio_model.pkl"
    if os.path.exists(model_path):
        predictor.load_model(model_path)
    else:
        print(f"⚠️ Modelo não encontrado em: {model_path}")
        print("   Use o endpoint POST /model/upload para enviar o modelo")


# ====================================================================
# ENDPOINTS - ROOT E HEALTH
# ====================================================================

@app.get("/", tags=["Root"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "HubFólio Data & ML API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "minio": {
                "upload": "/upload",
                "files": "/files",
                "ingest": "/ingest/hubfolio"
            },
            "postgres": {
                "summary": "/postgres/summary",
                "top_portfolios": "/postgres/top-portfolios"
            },
            "etl": {
                "run": "/etl/run"
            },
            "ml": {
                "predict": "/predict",
                "model_info": "/model/info"
            }
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verifica a saúde da API e conexões"""
    minio_connected = minio_client.check_connection()
    bucket_exists = minio_client.bucket_exists()
    postgres_connected = pg_client.check_connection() if pg_client else False
    
    return HealthResponse(
        status="healthy" if (minio_connected and bucket_exists and postgres_connected) else "partial",
        minio_connected=minio_connected,
        bucket_exists=bucket_exists,
        postgres_connected=postgres_connected,
        timestamp=datetime.utcnow().isoformat()
    )


# ====================================================================
# ENDPOINTS - MINIO (Data Ingestion)
# ====================================================================

@app.post("/upload", response_model=UploadResponse, tags=["Data Ingestion"])
async def upload_file(
    file: UploadFile = File(...),
    folder: Optional[str] = "raw"
):
    """Upload de arquivo para o MinIO"""
    try:
        contents = await file.read()
        file_size = len(contents)
        object_key = f"{folder}/{file.filename}"
        
        success = minio_client.upload_file(
            file_data=contents,
            object_name=object_key,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao fazer upload do arquivo para MinIO"
            )
        
        return UploadResponse(
            message="Arquivo enviado com sucesso!",
            filename=file.filename,
            size=file_size,
            bucket=minio_client.bucket_name,
            object_key=object_key
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload: {str(e)}"
        )


@app.get("/files", response_model=List[FileInfo], tags=["Data Management"])
async def list_files(prefix: Optional[str] = ""):
    """Lista arquivos no bucket do MinIO"""
    try:
        objects = minio_client.list_objects(prefix=prefix)
        
        files = []
        for obj in objects:
            files.append(FileInfo(
                filename=obj['Key'],
                size=obj['Size'],
                last_modified=obj['LastModified'].isoformat(),
                content_type=obj.get('ContentType', 'unknown')
            ))
        
        return files
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar arquivos: {str(e)}"
        )


@app.post("/ingest/hubfolio", tags=["Data Ingestion"])
async def ingest_hubfolio_dataset():
    """Ingere o dataset HubFólio completo para o MinIO"""
    try:
        data_file = "/data/archive/hubfolio_mock_data.json"
        
        if not os.path.exists(data_file):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo não encontrado: {data_file}"
            )
        
        # Ler arquivo
        with open(data_file, 'r', encoding='utf-8') as f:
            data = f.read()
        
        # Validar JSON
        json_data = json.loads(data)
        
        # Upload para MinIO
        object_key = "hubfolio/data/portfolios.json"
        success = minio_client.upload_file(
            file_data=data.encode('utf-8'),
            object_name=object_key,
            content_type="application/json"
        )
        
        if success:
            return {
                "message": "Ingestão do dataset HubFólio concluída",
                "object_key": object_key,
                "total_records": len(json_data),
                "size_bytes": len(data)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao enviar dados para MinIO"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante ingestão: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - POSTGRESQL
# ====================================================================

@app.get("/postgres/health", tags=["PostgreSQL"])
async def postgres_health():
    """Verifica conexão com PostgreSQL"""
    if not pg_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    connected = pg_client.check_connection()
    
    return {
        "postgres_connected": connected,
        "status": "healthy" if connected else "unhealthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/postgres/summary", tags=["PostgreSQL"])
async def get_database_summary():
    """Retorna sumário completo do banco de dados"""
    if not pg_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        table_info = pg_client.get_table_info()
        stats = pg_client.get_portfolio_stats()
        
        return {
            "database": "hubfolio",
            "tables": table_info,
            "statistics": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter sumário: {str(e)}"
        )


@app.get("/postgres/top-portfolios", tags=["PostgreSQL"])
async def get_top_portfolios(limit: int = 10):
    """Retorna os portfólios com maior IQ"""
    if not pg_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        portfolios = pg_client.get_top_portfolios(limit=limit)
        
        return {
            "total_results": len(portfolios),
            "top_portfolios": portfolios
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter top portfólios: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - ETL
# ====================================================================

@app.post("/etl/run", tags=["ETL"])
async def run_etl_pipeline():
    """Executa o pipeline ETL completo: MinIO -> PostgreSQL"""
    if not pg_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cliente PostgreSQL não inicializado"
        )
    
    try:
        # Executar ETL
        etl = HubFolioETL()
        stats = etl.run_full_etl()
        
        return {
            "message": "ETL executado com sucesso!",
            "status": stats.get("status", "unknown"),
            "statistics": {
                "users_inserted": stats.get("users_inserted", 0),
                "portfolios_inserted": stats.get("portfolios_inserted", 0),
                "metrics_calculated": stats.get("metrics_calculated", 0),
                "errors": stats.get("errors", 0),
                "duration_seconds": stats.get("duration_seconds", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar ETL: {str(e)}"
        )


# ====================================================================
# ENDPOINTS - MACHINE LEARNING
# ====================================================================

@app.post("/predict", response_model=PredictionResponse, tags=["Machine Learning"])
async def predict_portfolio_quality(portfolio: PortfolioInput):
    """
    Prediz o Índice de Qualidade de um portfólio e salva no PostgreSQL
    
    Fluxo:
    1. Verifica se user_id existe
    2. Realiza predição com modelo ML
    3. Salva portfólio e calcula métricas
    4. Salva predição
    """
    if not predictor.modelo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Modelo de ML não está carregado. Use POST /model/upload primeiro."
        )
    
    if not pg_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL não está disponível"
        )
    
    try:
        # Converter para dict
        dados = portfolio.dict()
        user_id = dados.get('user_id')
        
        # 1. VALIDAR SE USER_ID EXISTE
        if not pg_client.user_exists(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuário com ID {user_id} não encontrado no banco de dados. Por favor, verifique o user_id e tente novamente."
            )
        
        # 2. Realizar predição ANTES de inserir no banco
        # IMPORTANTE: Criar cópia para não alterar tipos de dados do original (bool -> int)
        dados_para_predicao = dados.copy()
        resultado = predictor.prever(dados_para_predicao)
        
        if not resultado.get("sucesso"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado.get("erro", "Erro desconhecido na predição")
            )
        
        # 3. Inserir portfólio no banco (portfolios + portfolio_metrics)
        # Usa 'dados' original que contém booleanos corretos
        try:
            portfolio_id = pg_client.create_portfolio_with_metrics(dados)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar portfólio no banco de dados: {str(e)}"
            )
        
        if not portfolio_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar portfólio no banco de dados (retornou None)"
            )
        
        # 4. Salvar predição no PostgreSQL
        prediction_id = pg_client.save_prediction(
            portfolio_id=portfolio_id,
            predicted_iq=resultado['indice_qualidade'],
            model_name=resultado['model_name'],
            classification=resultado.get('classificacao'),
            feedback=resultado.get('feedback')
        )
        
        # Adicionar IDs na resposta
        resultado['portfolio_id'] = portfolio_id
        resultado['prediction_id'] = prediction_id
        
        return PredictionResponse(**resultado)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro durante predição: {str(e)}"
        )


@app.get("/model/info", tags=["Machine Learning"])
async def get_model_info():
    """Retorna informações sobre o modelo carregado"""
    return {
        "model_loaded": predictor.modelo is not None,
        "model_name": predictor.model_name,
        "features": predictor.features,
        "num_features": len(predictor.features)
    }


@app.post("/model/upload", tags=["Machine Learning"])
async def upload_model(file: UploadFile = File(...)):
    """Upload do modelo treinado (.pkl)"""
    try:
        if not file.filename.endswith('.pkl'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Arquivo deve ser .pkl (modelo serializado com pickle)"
            )
        
        # Salvar arquivo
        model_path = "/app/models/hubfolio_model.pkl"
        os.makedirs("/app/models", exist_ok=True)
        
        contents = await file.read()
        with open(model_path, 'wb') as f:
            f.write(contents)
        
        # Carregar modelo
        if predictor.load_model(model_path):
            return {
                "message": "Modelo carregado com sucesso!",
                "model_path": model_path,
                "file_size": len(contents)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao carregar modelo"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload do modelo: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
