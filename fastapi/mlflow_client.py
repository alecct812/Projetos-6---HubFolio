"""
Cliente MLflow para HubFólio
Gerencia versionamento de modelos e experimentos
"""
import os
import logging
import pickle
from typing import Dict, Optional, Any
from datetime import datetime
import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import boto3
from botocore.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLflowClient:
    """Cliente para interagir com MLflow"""
    
    def __init__(self):
        self.tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        self.experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'hubfolio-models')
        
        # Configurar MLflow
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Configurar S3 endpoint para MinIO
        os.environ['MLFLOW_S3_ENDPOINT_URL'] = os.getenv(
            'MLFLOW_S3_ENDPOINT_URL', 
            'http://minio:9000'
        )
        
        # Configurar credenciais AWS para MinIO
        os.environ['AWS_ACCESS_KEY_ID'] = os.getenv(
            'MINIO_ACCESS_KEY',
            'grupo_hubfolio'
        )
        os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv(
            'MINIO_SECRET_KEY',
            'horse-lock-electric'
        )
        
        # Criar ou obter experimento
        try:
            self.experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if self.experiment is None:
                self.experiment_id = mlflow.create_experiment(self.experiment_name)
                logger.info(f"✅ Experimento '{self.experiment_name}' criado: {self.experiment_id}")
            else:
                self.experiment_id = self.experiment.experiment_id
                logger.info(f"✅ Experimento '{self.experiment_name}' encontrado: {self.experiment_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao configurar experimento MLflow: {e}")
            self.experiment_id = None
        
        # Inicializar cliente MLflow
        self.client = MlflowClient(tracking_uri=self.tracking_uri)
        
        logger.info(f"MLflow Client initialized - URI: {self.tracking_uri}")
    
    def check_connection(self) -> bool:
        """Verifica se a conexão com MLflow está OK"""
        try:
            experiments = mlflow.search_experiments()
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar com MLflow: {e}")
            return False
    
    def log_model(
        self,
        model: Any,
        model_name: str,
        metrics: Dict[str, float],
        parameters: Dict[str, Any] = None,
        tags: Dict[str, str] = None,
        artifact_path: str = "model"
    ) -> Optional[str]:
        """
        Registra modelo no MLflow
        
        Args:
            model: Modelo treinado (sklearn, etc.)
            model_name: Nome do modelo
            metrics: Dicionário com métricas (ex: {'r2_score': 0.85, 'rmse': 12.5})
            parameters: Parâmetros do modelo
            tags: Tags adicionais
            artifact_path: Caminho do artifact no MLflow
            
        Returns:
            run_id do experimento ou None
        """
        if not self.experiment_id:
            logger.error("Experimento não configurado")
            return None
        
        try:
            mlflow.set_experiment(self.experiment_name)
            
            with mlflow.start_run() as run:
                # Log do modelo
                mlflow.sklearn.log_model(
                    model,
                    artifact_path=artifact_path
                )
                
                # Log de métricas
                for metric_name, metric_value in metrics.items():
                    mlflow.log_metric(metric_name, metric_value)
                
                # Log de parâmetros
                if parameters:
                    for param_name, param_value in parameters.items():
                        mlflow.log_param(param_name, str(param_value))
                
                # Log de tags
                if tags:
                    for tag_name, tag_value in tags.items():
                        mlflow.set_tag(tag_name, str(tag_value))
                
                # Tag de timestamp
                mlflow.set_tag("registered_at", datetime.utcnow().isoformat())
                mlflow.set_tag("model_type", type(model).__name__)
                
                run_id = run.info.run_id
                logger.info(f"✅ Modelo '{model_name}' registrado no MLflow - Run ID: {run_id}")
                
                return run_id
                
        except Exception as e:
            logger.error(f"❌ Erro ao registrar modelo no MLflow: {e}")
            return None
    
    def register_model_version(
        self,
        model_name: str,
        run_id: str,
        stage: str = "Production",
        description: str = None
    ) -> Optional[str]:
        """
        Registra uma versão do modelo no Model Registry
        
        Args:
            model_name: Nome do modelo
            run_id: ID do run do MLflow
            stage: Stage do modelo (Staging, Production, Archived)
            
        Returns:
            version do modelo ou None
        """
        try:
            # Criar modelo registrado se não existir
            try:
                self.client.create_registered_model(model_name)
                logger.info(f"✅ Modelo '{model_name}' criado no Model Registry")
            except Exception as e:
                # Modelo já existe, continuar
                logger.debug(f"Modelo '{model_name}' já existe: {e}")
                pass
            
            # Registrar versão
            model_uri = f"runs:/{run_id}/model"
            model_version = mlflow.register_model(
                model_uri,
                model_name
            )
            
            # Adicionar descrição se fornecida
            if description:
                try:
                    self.client.update_model_version(
                        name=model_name,
                        version=model_version.version,
                        description=description
                    )
                    logger.info(f"✅ Descrição adicionada à versão {model_version.version}")
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao adicionar descrição: {e}")
            
            # Transicionar para stage
            if stage:
                try:
                    self.client.transition_model_version_stage(
                        name=model_name,
                        version=model_version.version,
                        stage=stage
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao transicionar para stage '{stage}': {e}")
            
            logger.info(f"✅ Versão {model_version.version} do modelo '{model_name}' registrada no stage '{stage}'")
            return str(model_version.version)
            
        except Exception as e:
            logger.error(f"❌ Erro ao registrar versão do modelo: {e}")
            return None
    
    def get_latest_model(self, model_name: str, stage: str = "Production") -> Optional[Any]:
        """
        Obtém o modelo mais recente de um stage específico
        
        Args:
            model_name: Nome do modelo
            stage: Stage do modelo
            
        Returns:
            Modelo carregado ou None
        """
        try:
            model_uri = f"models:/{model_name}/{stage}"
            model = mlflow.sklearn.load_model(model_uri)
            logger.info(f"✅ Modelo '{model_name}' (stage: {stage}) carregado do MLflow")
            return model
        except Exception as e:
            logger.error(f"❌ Erro ao carregar modelo do MLflow: {e}")
            return None
    
    def export_model_to_s3(
        self,
        model_name: str,
        stage: str = "Production",
        s3_bucket: str = "hubfolio-data",
        s3_key: str = None
    ) -> Optional[str]:
        """
        Exporta modelo do MLflow para S3 (MinIO)
        
        Args:
            model_name: Nome do modelo no MLflow
            stage: Stage do modelo
            s3_bucket: Bucket do S3/MinIO
            s3_key: Chave do objeto no S3 (se None, usa nome padrão)
            
        Returns:
            S3 key do modelo exportado ou None
        """
        try:
            # Carregar modelo do MLflow
            model = self.get_latest_model(model_name, stage)
            if model is None:
                return None
            
            # Obter informações da versão
            latest_version = self.client.get_latest_versions(model_name, stages=[stage])
            if not latest_version:
                logger.error(f"Nenhuma versão encontrada para modelo '{model_name}' no stage '{stage}'")
                return None
            
            version_info = latest_version[0]
            version = version_info.version
            
            # Gerar S3 key se não fornecido
            if s3_key is None:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                s3_key = f"models/{model_name}/v{version}/{model_name}_v{version}_{timestamp}.pkl"
            
            # Serializar modelo
            model_bytes = pickle.dumps(model)
            
            # Upload para S3/MinIO
            minio_endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
            minio_access_key = os.getenv('MINIO_ACCESS_KEY', 'grupo_hubfolio')
            minio_secret_key = os.getenv('MINIO_SECRET_KEY', 'horse-lock-electric')
            
            s3_client = boto3.client(
                's3',
                endpoint_url=f'http://{minio_endpoint}',
                aws_access_key_id=minio_access_key,
                aws_secret_access_key=minio_secret_key,
                config=Config(signature_version='s3v4'),
                region_name='us-east-1'
            )
            
            s3_client.put_object(
                Bucket=s3_bucket,
                Key=s3_key,
                Body=model_bytes,
                ContentType='application/octet-stream'
            )
            
            logger.info(f"✅ Modelo '{model_name}' v{version} exportado para S3: s3://{s3_bucket}/{s3_key}")
            return s3_key
            
        except Exception as e:
            logger.error(f"❌ Erro ao exportar modelo para S3: {e}")
            return None
    
    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """
        Obtém informações sobre um modelo registrado
        
        Args:
            model_name: Nome do modelo
            
        Returns:
            Dicionário com informações do modelo ou None
        """
        try:
            model_info = self.client.get_registered_model(model_name)
            
            latest_versions = []
            for version in model_info.latest_versions:
                latest_versions.append({
                    'version': version.version,
                    'stage': version.current_stage,
                    'run_id': version.run_id,
                    'created_at': version.creation_timestamp.isoformat() if version.creation_timestamp else None
                })
            
            return {
                'name': model_info.name,
                'latest_versions': latest_versions,
                'created_at': model_info.creation_timestamp.isoformat() if model_info.creation_timestamp else None
            }
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações do modelo: {e}")
            return None

