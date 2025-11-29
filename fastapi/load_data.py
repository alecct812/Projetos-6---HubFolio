"""
Script de Carga Inicial de Dados
Carrega hubfolio_mock_data.json para o MinIO
"""
import os
import json
import logging
from minio_client import MinIOClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_data_to_minio():
    """Carrega dados do arquivo JSON para o MinIO"""
    
    # Inicializar cliente
    minio_client = MinIOClient()
    
    # Verificar conexão
    if not minio_client.check_connection():
        logger.error("❌ MinIO não está acessível")
        return False
    
    # Criar bucket se não existir
    minio_client.create_bucket_if_not_exists()
    
    # Caminho do arquivo de dados
    data_file = "/data/archive/hubfolio_mock_data.json"
    
    if not os.path.exists(data_file):
        logger.error(f"❌ Arquivo não encontrado: {data_file}")
        return False
    
    # Ler arquivo
    logger.info(f"📖 Lendo arquivo: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = f.read()
    
    # Validar JSON
    try:
        json_data = json.loads(data)
        logger.info(f"✅ JSON válido com {len(json_data)} registros")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON inválido: {e}")
        return False
    
    # Upload para MinIO
    object_name = "hubfolio/data/portfolios.json"
    logger.info(f"📤 Fazendo upload para MinIO: {object_name}")
    
    success = minio_client.upload_file(
        file_data=data.encode('utf-8'),
        object_name=object_name,
        content_type="application/json"
    )
    
    if success:
        logger.info(f"✅ Upload concluído com sucesso!")
        logger.info(f"   Bucket: {minio_client.bucket_name}")
        logger.info(f"   Object: {object_name}")
        logger.info(f"   Tamanho: {len(data)} bytes")
        logger.info(f"   Registros: {len(json_data)}")
        return True
    else:
        logger.error("❌ Falha no upload")
        return False


if __name__ == "__main__":
    import time
    
    # Aguardar MinIO inicializar (quando rodando no Docker)
    logger.info("⏳ Aguardando MinIO inicializar...")
    time.sleep(5)
    
    # Executar carga
    success = load_data_to_minio()
    
    if success:
        logger.info("="*60)
        logger.info("🎉 CARGA DE DADOS CONCLUÍDA COM SUCESSO!")
        logger.info("="*60)
        exit(0)
    else:
        logger.error("="*60)
        logger.error("❌ FALHA NA CARGA DE DADOS")
        logger.error("="*60)
        exit(1)
