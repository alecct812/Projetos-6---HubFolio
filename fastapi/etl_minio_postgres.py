"""
ETL Script: MinIO -> PostgreSQL
Extrai dados do MinIO e carrega no PostgreSQL de forma estruturada
"""

import io
import json
import logging
from datetime import datetime
from typing import Dict, List
import pandas as pd

from minio_client import MinIOClient
from postgres_client import PostgreSQLClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HubFolioETL:
    """Pipeline ETL para transferir dados do MinIO para PostgreSQL"""
    
    def __init__(self):
        self.minio_client = MinIOClient()
        self.pg_client = PostgreSQLClient()
        self.stats = {
            "users_inserted": 0,
            "portfolios_inserted": 0,
            "metrics_calculated": 0,
            "errors": 0
        }
    
    def extract_from_minio(self, object_name: str) -> bytes:
        """
        Extrai dados de um arquivo no MinIO
        
        Args:
            object_name: Caminho do objeto no MinIO (ex: 'hubfolio/data/portfolios.json')
            
        Returns:
            Bytes com os dados do arquivo
        """
        try:
            logger.info(f"Extraindo dados de {object_name}")
            
            # Download do objeto usando boto3 (s3_client)
            response = self.minio_client.s3_client.get_object(
                Bucket=self.minio_client.bucket_name,
                Key=object_name
            )
            
            # Ler conteúdo
            data = response['Body'].read()
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de {object_name}: {e}")
            raise
    
    def load_portfolios(self) -> int:
        """
        Carrega portfólios do MinIO para PostgreSQL
        
        Returns:
            Número de portfólios inseridos
        """
        try:
            logger.info("Iniciando carga de portfólios...")
            
            # Extrair dados
            data = self.extract_from_minio("hubfolio/data/portfolios.json")
            
            # Parsear JSON
            portfolios = json.loads(data.decode('utf-8'))
            
            logger.info(f"Total de {len(portfolios)} portfólios encontrados")
            
            inserted_portfolios = 0
            inserted_users = 0
            metrics_calculated = 0
            
            for portfolio in portfolios:
                try:
                    # 1. Inserir usuário
                    user_data = {
                        'user_id': portfolio['user_id'],
                        'nome': portfolio['nome']
                    }
                    
                    user_id = self.pg_client.insert_user(user_data)
                    if user_id:
                        inserted_users += 1
                    
                    # 2. Inserir portfólio
                    portfolio_data = {
                        'user_id': portfolio['user_id'],
                        'bio': portfolio['secoes_preenchidas']['bio'],
                        'projetos_min': portfolio['secoes_preenchidas']['projetos_min'],
                        'habilidades_min': portfolio['secoes_preenchidas']['habilidades_min'],
                        'contatos': portfolio['secoes_preenchidas']['contatos'],
                        'kw_contexto': portfolio['palavras_chave_clareza']['contexto'],
                        'kw_processo': portfolio['palavras_chave_clareza']['processo'],
                        'kw_resultado': portfolio['palavras_chave_clareza']['resultado'],
                        'consistencia_visual_score': portfolio['consistencia_visual_score']
                    }
                    
                    portfolio_id = self.pg_client.insert_portfolio(portfolio_data)
                    if portfolio_id:
                        inserted_portfolios += 1
                        
                        # 3. Calcular métricas
                        if self.pg_client.calculate_metrics(portfolio_id):
                            metrics_calculated += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar portfólio {portfolio.get('user_id')}: {e}")
                    self.stats["errors"] += 1
            
            self.stats["users_inserted"] = inserted_users
            self.stats["portfolios_inserted"] = inserted_portfolios
            self.stats["metrics_calculated"] = metrics_calculated
            
            logger.info(f"✓ {inserted_users} usuários inseridos")
            logger.info(f"✓ {inserted_portfolios} portfólios inseridos")
            logger.info(f"✓ {metrics_calculated} métricas calculadas")
            
            return inserted_portfolios
            
        except Exception as e:
            logger.error(f"Erro ao carregar portfólios: {e}")
            raise
    
    def run_full_etl(self) -> Dict:
        """
        Executa o pipeline ETL completo
        
        Returns:
            Dicionário com estatísticas da execução
        """
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Iniciando ETL: MinIO -> PostgreSQL (HubFólio)")
        logger.info("="*60)
        
        try:
            # Verificar conexões
            if not self.minio_client.check_connection():
                raise Exception("MinIO não está conectado")
            
            if not self.pg_client.check_connection():
                raise Exception("PostgreSQL não está conectado")
            
            # Carregar portfólios
            self.load_portfolios()
            
            # Calcular tempo de execução
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Estatísticas finais
            self.stats["duration_seconds"] = duration
            self.stats["status"] = "success"
            
            logger.info("="*60)
            logger.info("ETL CONCLUÍDO COM SUCESSO!")
            logger.info(f"Usuários inseridos: {self.stats['users_inserted']}")
            logger.info(f"Portfólios inseridos: {self.stats['portfolios_inserted']}")
            logger.info(f"Métricas calculadas: {self.stats['metrics_calculated']}")
            logger.info(f"Erros: {self.stats['errors']}")
            logger.info(f"Tempo de execução: {duration:.2f}s")
            logger.info("="*60)
            
            return self.stats
            
        except Exception as e:
            logger.error(f"ERRO NO ETL: {e}")
            self.stats["status"] = "failed"
            self.stats["error_message"] = str(e)
            raise
    
    def get_summary(self) -> Dict:
        """Retorna sumário dos dados no PostgreSQL"""
        try:
            table_info = self.pg_client.get_table_info()
            stats = self.pg_client.get_portfolio_stats()
            
            return {
                "tables": table_info,
                "statistics": stats
            }
        except Exception as e:
            logger.error(f"Erro ao obter sumário: {e}")
            return {}


def main():
    """Função principal para execução do ETL via CLI"""
    etl = HubFolioETL()
    
    try:
        # Executar ETL completo
        stats = etl.run_full_etl()
        
        # Exibir sumário
        print("\n📊 SUMÁRIO DO BANCO DE DADOS:")
        summary = etl.get_summary()
        
        if 'tables' in summary:
            print("\n📋 Contagem por Tabela:")
            for table, count in summary['tables'].items():
                print(f"  {table}: {count}")
        
        if 'statistics' in summary:
            print("\n📈 Estatísticas dos Portfólios:")
            for key, value in summary['statistics'].items():
                if value is not None:
                    print(f"  {key}: {value}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Falha na execução do ETL: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
