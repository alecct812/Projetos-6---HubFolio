"""
FastAPI - Sistema de Ingestão e Predição HubFólio
API para gerenciamento de dados e inferência do modelo de ML
"""
import os
import json
import pickle
import logging
from typing import List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np

from minio_client import MinIOClient
from postgres_client import PostgreSQLClient
from etl_minio_postgres import HubFolioETL
from mlflow_client import MLflowClient
from thingsboard_client import ThingsBoardClient

# Inicializar FastAPI
app = FastAPI(
    title="HubFólio Data & ML API",
    description="API para ingestão de dados e predição de Índice de Qualidade de Portfólios",
    version="1.0.0"
)

# Inicializar clientes
minio_client = MinIOClient()
pg_client = None  # Será inicializado no startup
mlflow_client = None  # Será inicializado no startup
tb_client = None  # Será inicializado no startup


# ====================================================================
# MODELOS PYDANTIC
# ====================================================================

class HealthResponse(BaseModel):
    status: str
    minio_connected: bool
    bucket_exists: bool
    postgres_connected: bool
    mlflow_connected: Optional[bool] = None
    thingsboard_connected: Optional[bool] = None
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
    global pg_client, predictor, mlflow_client, tb_client
    
    # MinIO
    minio_client.create_bucket_if_not_exists()
    print(f"✅ Bucket '{minio_client.bucket_name}' verificado/criado com sucesso!")
    
    # Criar bucket mlflow-artifacts se não existir
    try:
        import boto3
        from botocore.config import Config
        s3_client = boto3.client(
            's3',
            endpoint_url=f'http://{os.getenv("MINIO_ENDPOINT", "minio:9000")}',
            aws_access_key_id=os.getenv('MINIO_ACCESS_KEY', 'grupo_hubfolio'),
            aws_secret_access_key=os.getenv('MINIO_SECRET_KEY', 'horse-lock-electric'),
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        try:
            s3_client.head_bucket(Bucket='mlflow-artifacts')
            print(f"✅ Bucket 'mlflow-artifacts' já existe")
        except:
            s3_client.create_bucket(Bucket='mlflow-artifacts')
            print(f"✅ Bucket 'mlflow-artifacts' criado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao criar bucket mlflow-artifacts: {e}")
    
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
    
    # MLflow
    try:
        mlflow_client = MLflowClient()
        if mlflow_client.check_connection():
            print(f"✅ MLflow conectado com sucesso!")
        else:
            print(f"⚠️ MLflow não está acessível")
    except Exception as e:
        print(f"⚠️ Erro ao conectar MLflow: {e}")
        mlflow_client = None
    
    # ThingsBoard
    try:
        tb_client = ThingsBoardClient()
        if tb_client.check_connection():
            print(f"✅ ThingsBoard conectado com sucesso!")
        else:
            print(f"⚠️ ThingsBoard não está acessível (pode ser normal se não configurado)")
    except Exception as e:
        print(f"⚠️ Erro ao conectar ThingsBoard: {e}")
        tb_client = None
    
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
                "model_info": "/model/info",
                "model_upload": "/model/upload",
                "export_to_s3": "/model/export-to-s3"
            }
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Verifica a saúde da API e conexões"""
    minio_connected = minio_client.check_connection()
    bucket_exists = minio_client.bucket_exists()
    postgres_connected = pg_client.check_connection() if pg_client else False
    mlflow_connected = mlflow_client.check_connection() if mlflow_client else False
    tb_connected = tb_client.check_connection() if tb_client else False
    
    all_connected = (minio_connected and bucket_exists and postgres_connected)
    
    return {
        "status": "healthy" if all_connected else "partial",
        "minio_connected": minio_connected,
        "bucket_exists": bucket_exists,
        "postgres_connected": postgres_connected,
        "mlflow_connected": mlflow_connected,
        "thingsboard_connected": tb_connected,
        "timestamp": datetime.utcnow().isoformat()
    }


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
        
        # Enviar dados para ThingsBoard se disponível
        if tb_client:
            try:
                device_token = os.getenv('THINGSBOARD_DEVICE_TOKEN', 'hubfolio-device-token')
                tb_client.send_prediction_data(
                    device_token=device_token,
                    prediction_data={
                        'portfolio_id': portfolio_id,
                        'predicted_iq': resultado['indice_qualidade'],
                        'classification': resultado['classificacao'],
                        'model_name': resultado['model_name'],
                        'user_id': user_id,
                        'prediction_id': prediction_id
                    }
                )
            except Exception as e:
                logger.warning(f"Erro ao enviar dados para ThingsBoard: {e}")
        
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
    """Retorna informações sobre o modelo carregado e no MLflow"""
    info = {
        "model_loaded": predictor.modelo is not None,
        "model_name": predictor.model_name,
        "features": predictor.features,
        "num_features": len(predictor.features)
    }
    
    # Adicionar informações do MLflow se disponível
    if mlflow_client:
        try:
            model_info = mlflow_client.get_model_info("hubfolio-model")
            if model_info:
                info["mlflow"] = model_info
        except Exception as e:
            logger.warning(f"Erro ao obter informações do MLflow: {e}")
    
    return info


@app.post("/model/upload", tags=["Machine Learning"])
async def upload_model(
    file: UploadFile = File(...),
    model_name: Optional[str] = Form("hubfolio-model"),
    r2_score: Optional[float] = Form(None),
    rmse: Optional[float] = Form(None),
    mae: Optional[float] = Form(None),
    register_in_mlflow: bool = Form(True),
    export_to_s3: bool = Form(True)
):
    """
    Upload do modelo treinado (.pkl) com versionamento no MLflow e exportação para S3
    
    Parâmetros opcionais:
    - model_name: Nome do modelo no MLflow (padrão: "hubfolio-model")
    - r2_score: R² score do modelo (para registro no MLflow)
    - rmse: RMSE do modelo (para registro no MLflow)
    - mae: MAE do modelo (para registro no MLflow)
    - register_in_mlflow: Se True, registra no MLflow (padrão: True)
    - export_to_s3: Se True, exporta para S3 após registro (padrão: True)
    """
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
        if not predictor.load_model(model_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao carregar modelo"
            )
        
        response_data = {
            "message": "Modelo carregado com sucesso!",
            "model_path": model_path,
            "file_size": len(contents),
            "mlflow_registered": False,
            "s3_exported": False
        }
        
        # Registrar no MLflow se solicitado
        if register_in_mlflow and mlflow_client:
            try:
                # Carregar modelo para registro
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Preparar métricas
                metrics = {}
                logger.info(f"📊 DEBUG - Parâmetros recebidos: r2_score={r2_score} (type: {type(r2_score)}), rmse={rmse} (type: {type(rmse)}), mae={mae} (type: {type(mae)})")
                
                # Converter strings para float se necessário
                if r2_score is not None and r2_score != "" and str(r2_score).lower() != "none":
                    try:
                        metrics['r2_score'] = float(r2_score)
                        logger.info(f"✅ R² Score adicionado: {metrics['r2_score']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Erro ao converter r2_score: {e}")
                
                if rmse is not None and rmse != "" and str(rmse).lower() != "none":
                    try:
                        metrics['rmse'] = float(rmse)
                        logger.info(f"✅ RMSE adicionado: {metrics['rmse']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Erro ao converter rmse: {e}")
                
                if mae is not None and mae != "" and str(mae).lower() != "none":
                    try:
                        metrics['mae'] = float(mae)
                        logger.info(f"✅ MAE adicionado: {metrics['mae']}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Erro ao converter mae: {e}")
                
                # Se não houver métricas, avisar mas não usar valores zerados
                if not metrics:
                    logger.warning("⚠️ Nenhuma métrica fornecida. Use r2_score, rmse, mae como parâmetros.")
                    metrics = {
                        'r2_score': 0.0,
                        'rmse': 0.0,
                        'mae': 0.0
                    }
                    response_data["warning"] = "Métricas não fornecidas - valores zerados serão registrados. Faça upload novamente com métricas para corrigir."
                
                # Registrar modelo
                run_id = mlflow_client.log_model(
                    model=model,
                    model_name=model_name,
                    metrics=metrics,
                    parameters={
                        'model_type': type(model).__name__,
                        'features_count': len(predictor.features)
                    },
                    tags={
                        'uploaded_at': datetime.utcnow().isoformat(),
                        'source': 'api_upload'
                    }
                )
                
                # Adicionar descrição ao modelo se houver métricas
                if metrics and any(v > 0 for v in metrics.values()):
                    description = f"Modelo {model_name} - "
                    desc_parts = []
                    if metrics.get('r2_score', 0) > 0:
                        desc_parts.append(f"R²: {metrics['r2_score']:.3f}")
                    if metrics.get('rmse', 0) > 0:
                        desc_parts.append(f"RMSE: {metrics['rmse']:.2f}")
                    if metrics.get('mae', 0) > 0:
                        desc_parts.append(f"MAE: {metrics['mae']:.2f}")
                    if desc_parts:
                        description += " | ".join(desc_parts)
                    else:
                        description += "Upload via API"
                else:
                    description = f"Modelo {model_name} - Upload via API (métricas não fornecidas)"
                
                if run_id:
                    # Preparar descrição
                    description = None
                    if metrics and any(v > 0 for v in metrics.values()):
                        desc_parts = []
                        if metrics.get('r2_score', 0) > 0:
                            desc_parts.append(f"R²: {metrics['r2_score']:.3f}")
                        if metrics.get('rmse', 0) > 0:
                            desc_parts.append(f"RMSE: {metrics['rmse']:.2f}")
                        if metrics.get('mae', 0) > 0:
                            desc_parts.append(f"MAE: {metrics['mae']:.2f}")
                        if desc_parts:
                            description = " | ".join(desc_parts)
                    
                    # Registrar versão no Model Registry
                    version = mlflow_client.register_model_version(
                        model_name=model_name,
                        run_id=run_id,
                        stage="Production",
                        description=description
                    )
                    
                    response_data["mlflow_registered"] = True
                    response_data["mlflow_run_id"] = run_id
                    response_data["mlflow_model_version"] = version
                    
                    # Exportar para S3 se solicitado
                    if export_to_s3:
                        s3_key = mlflow_client.export_model_to_s3(
                            model_name=model_name,
                            stage="Production"
                        )
                        if s3_key:
                            response_data["s3_exported"] = True
                            response_data["s3_key"] = s3_key
                
            except Exception as e:
                logger.error(f"Erro ao registrar modelo no MLflow: {e}")
                response_data["mlflow_error"] = str(e)
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar upload do modelo: {str(e)}"
        )


@app.post("/model/export-to-s3", tags=["Machine Learning"])
async def export_model_to_s3(
    model_name: str = "hubfolio-model",
    stage: str = "Production"
):
    """
    Exporta modelo do MLflow para S3 (MinIO)
    
    Args:
        model_name: Nome do modelo no MLflow
        stage: Stage do modelo (Production, Staging, Archived)
    """
    if not mlflow_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MLflow não está disponível"
        )
    
    try:
        s3_key = mlflow_client.export_model_to_s3(
            model_name=model_name,
            stage=stage
        )
        
        if s3_key:
            return {
                "message": "Modelo exportado para S3 com sucesso!",
                "model_name": model_name,
                "stage": stage,
                "s3_key": s3_key
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao exportar modelo para S3"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao exportar modelo para S3: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
