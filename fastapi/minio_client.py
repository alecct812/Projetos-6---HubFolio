"""
Cliente MinIO/S3 para HubFólio
Gerencia upload e download de dados no object storage
"""
import os
import io
import logging
from typing import List, Dict, Optional
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MinIOClient:
    """Cliente para interagir com MinIO (S3-compatible object storage)"""
    
    def __init__(self):
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'hubfolio_admin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'hubfolio_secret_2025')
        self.bucket_name = os.getenv('MINIO_BUCKET', 'hubfolio-data')
        
        # Criar cliente boto3 (S3)
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'http://{self.endpoint}',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=boto3.session.Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
        
        logger.info(f"MinIO Client initialized - Endpoint: {self.endpoint}, Bucket: {self.bucket_name}")
    
    def check_connection(self) -> bool:
        """Verifica se a conexão com MinIO está OK"""
        try:
            self.s3_client.list_buckets()
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar com MinIO: {e}")
            return False
    
    def bucket_exists(self) -> bool:
        """Verifica se o bucket existe"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
    
    def create_bucket_if_not_exists(self) -> bool:
        """Cria o bucket se não existir"""
        try:
            if not self.bucket_exists():
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' criado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao criar bucket: {e}")
            return False
    
    def upload_file(
        self, 
        file_data: bytes, 
        object_name: str,
        content_type: str = 'application/json'
    ) -> bool:
        """
        Faz upload de arquivo para o MinIO
        
        Args:
            file_data: Dados do arquivo em bytes
            object_name: Nome do objeto no bucket (path)
            content_type: Tipo MIME do arquivo
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=file_data,
                ContentType=content_type
            )
            logger.info(f"Upload bem-sucedido: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Erro no upload de {object_name}: {e}")
            return False
    
    def download_file(self, object_name: str) -> Optional[bytes]:
        """
        Baixa arquivo do MinIO
        
        Args:
            object_name: Nome do objeto no bucket
            
        Returns:
            Bytes do arquivo ou None se erro
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            data = response['Body'].read()
            logger.info(f"Download bem-sucedido: {object_name}")
            return data
        except Exception as e:
            logger.error(f"Erro no download de {object_name}: {e}")
            return None
    
    def list_objects(self, prefix: str = '') -> List[Dict]:
        """
        Lista objetos no bucket
        
        Args:
            prefix: Filtro de prefixo (pasta)
            
        Returns:
            Lista de dicionários com informações dos objetos
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            objects = []
            for obj in response['Contents']:
                objects.append({
                    'Key': obj['Key'],
                    'Size': obj['Size'],
                    'LastModified': obj['LastModified'],
                    'ContentType': obj.get('ContentType', 'unknown')
                })
            
            return objects
        except Exception as e:
            logger.error(f"Erro ao listar objetos: {e}")
            return []
    
    def delete_file(self, object_name: str) -> bool:
        """
        Remove arquivo do MinIO
        
        Args:
            object_name: Nome do objeto no bucket
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"Arquivo removido: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover {object_name}: {e}")
            return False
    
    def get_object_metadata(self, object_name: str) -> Optional[Dict]:
        """
        Obtém metadados de um objeto
        
        Args:
            object_name: Nome do objeto
            
        Returns:
            Dicionário com metadados ou None
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return {
                'ContentLength': response['ContentLength'],
                'ContentType': response.get('ContentType'),
                'LastModified': response['LastModified'],
                'ETag': response['ETag']
            }
        except Exception as e:
            logger.error(f"Erro ao obter metadados de {object_name}: {e}")
            return None
