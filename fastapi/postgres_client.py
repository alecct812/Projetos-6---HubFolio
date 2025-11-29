"""
Cliente PostgreSQL para HubFólio
Gerencia operações de banco de dados
"""
import os
import logging
from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgreSQLClient:
    """Cliente para interagir com PostgreSQL"""
    
    def __init__(self):
        self.host = os.getenv('POSTGRES_HOST', 'localhost')
        self.port = int(os.getenv('POSTGRES_PORT', 5432))
        self.database = os.getenv('POSTGRES_DB', 'hubfolio')
        self.user = os.getenv('POSTGRES_USER', 'hubfolio_user')
        self.password = os.getenv('POSTGRES_PASSWORD', 'hubfolio_password_2025')
        
        self.conn_params = {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }
        
        logger.info(f"PostgreSQL Client initialized - Host: {self.host}, DB: {self.database}")
    
    def get_connection(self):
        """Cria conexão com PostgreSQL"""
        try:
            return psycopg2.connect(**self.conn_params)
        except Exception as e:
            logger.error(f"Erro ao conectar PostgreSQL: {e}")
            raise
    
    def check_connection(self) -> bool:
        """Verifica se a conexão está OK"""
        try:
            conn = self.get_connection()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erro na verificação de conexão: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Executa query SELECT e retorna resultados
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            
        Returns:
            Lista de dicionários com resultados
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Erro ao executar query: {e}")
            return []
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """
        Executa INSERT e retorna ID inserido
        
        Args:
            query: Query SQL INSERT
            params: Parâmetros da query
            
        Returns:
            ID do registro inserido ou None
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Tentar obter ID retornado
            inserted_id = None
            if cursor.description:
                result = cursor.fetchone()
                if result:
                    inserted_id = result[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return inserted_id
        except Exception as e:
            logger.error(f"Erro ao executar INSERT: {e}")
            return None
    
    def get_tables(self) -> List[str]:
        """Retorna lista de tabelas no banco"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        results = self.execute_query(query)
        return [row['table_name'] for row in results]
    
    def get_table_info(self) -> Dict[str, int]:
        """Retorna contagem de registros por tabela"""
        tables = self.get_tables()
        info = {}
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = self.execute_query(query)
            if result:
                info[table] = result[0]['count']
        
        return info
    
    # ====================================================================
    # OPERAÇÕES ESPECÍFICAS HUBFÓLIO
    # ====================================================================
    
    def insert_user(self, user_data: Dict) -> Optional[int]:
        """Insere usuário"""
        query = """
        INSERT INTO users (user_id, nome)
        VALUES (%(user_id)s, %(nome)s)
        ON CONFLICT (user_id) DO UPDATE SET nome = EXCLUDED.nome
        RETURNING user_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, user_data)
            user_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return user_id
        except Exception as e:
            logger.error(f"Erro ao inserir usuário: {e}")
            return None
    
    def insert_portfolio(self, portfolio_data: Dict) -> Optional[int]:
        """Insere portfólio"""
        query = """
        INSERT INTO portfolios (
            user_id, bio, projetos_min, habilidades_min, contatos,
            kw_contexto, kw_processo, kw_resultado, consistencia_visual_score
        )
        VALUES (
            %(user_id)s, %(bio)s, %(projetos_min)s, %(habilidades_min)s, %(contatos)s,
            %(kw_contexto)s, %(kw_processo)s, %(kw_resultado)s, %(consistencia_visual_score)s
        )
        RETURNING portfolio_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, portfolio_data)
            portfolio_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return portfolio_id
        except Exception as e:
            logger.error(f"Erro ao inserir portfólio: {e}")
            return None
    
    def calculate_metrics(self, portfolio_id: int) -> bool:
        """Calcula métricas de um portfólio"""
        query = "SELECT calculate_portfolio_metrics(%s)"
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (portfolio_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erro ao calcular métricas: {e}")
            return False
    
    def insert_prediction(self, prediction_data: Dict) -> Optional[int]:
        """Insere predição do modelo"""
        query = """
        INSERT INTO predictions (
            portfolio_id, predicted_iq, model_name, model_version,
            classification, feedback_suggestions
        )
        VALUES (
            %(portfolio_id)s, %(predicted_iq)s, %(model_name)s, %(model_version)s,
            %(classification)s, %(feedback_suggestions)s
        )
        RETURNING prediction_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, prediction_data)
            prediction_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return prediction_id
        except Exception as e:
            logger.error(f"Erro ao inserir predição: {e}")
            return None
    
    def get_portfolio_summary(self, limit: int = 100) -> List[Dict]:
        """Retorna sumário de portfólios"""
        query = f"SELECT * FROM portfolio_summary ORDER BY indice_qualidade DESC LIMIT {limit}"
        return self.execute_query(query)
    
    def get_portfolio_stats(self) -> Dict:
        """Retorna estatísticas gerais"""
        query = "SELECT * FROM portfolio_stats"
        results = self.execute_query(query)
        return results[0] if results else {}
    
    def get_top_portfolios(self, limit: int = 10) -> List[Dict]:
        """Retorna top portfólios"""
        query = f"SELECT * FROM top_portfolios LIMIT {limit}"
        return self.execute_query(query)
    
    def user_exists(self, user_id: int) -> bool:
        """
        Verifica se um usuário existe no banco de dados
        
        Args:
            user_id: ID do usuário a verificar
            
        Returns:
            True se o usuário existe, False caso contrário
        """
        query = "SELECT COUNT(*) as count FROM users WHERE user_id = %s"
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] > 0 if result else False
        except Exception as e:
            logger.error(f"Erro ao verificar existência do usuário {user_id}: {e}")
            return False
    
    def create_portfolio_with_metrics(self, portfolio_data: Dict) -> Optional[int]:
        """
        Cria um portfólio e calcula métricas automaticamente
        
        Args:
            portfolio_data: Dicionário com dados do portfólio (deve incluir user_id)
            
        Returns:
            portfolio_id do registro criado ou None
        """
        portfolio_query = """
        INSERT INTO portfolios (
            user_id, bio, projetos_min, habilidades_min, contatos,
            kw_contexto, kw_processo, kw_resultado, consistencia_visual_score
        )
        VALUES (
            %(user_id)s, %(bio)s, %(projetos_min)s, %(habilidades_min)s, %(contatos)s,
            %(kw_contexto)s, %(kw_processo)s, %(kw_resultado)s, %(consistencia_visual_score)s
        )
        RETURNING portfolio_id
        """
        
        metrics_query = "SELECT calculate_portfolio_metrics(%s)"
        
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Criar portfólio
            cursor.execute(portfolio_query, portfolio_data)
            portfolio_id = cursor.fetchone()[0]
            
            # Calcular métricas automaticamente
            cursor.execute(metrics_query, (portfolio_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Portfólio criado: ID={portfolio_id}, User={portfolio_data.get('user_id')} (com métricas)")
            return portfolio_id
        except Exception as e:
            if conn:
                conn.rollback()
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                try:
                    conn.close()
                except:
                    pass
            logger.error(f"❌ Erro ao criar portfólio: {e}")
            raise  # Re-raise para debug no main.py
    
    def save_prediction(self, portfolio_id: int, predicted_iq: float, model_name: str, 
                       classification: str = None, feedback: List[str] = None) -> Optional[int]:
        """
        Salva predição no banco de dados COM portfolio_id
        
        Args:
            portfolio_id: ID do portfólio avaliado
            predicted_iq: IQ previsto pelo modelo
            model_name: Nome do modelo usado
            classification: Classificação (Excelente, Bom, etc.)
            feedback: Lista de sugestões de melhoria
            
        Returns:
            ID da predição inserida ou None
        """
        query = """
        INSERT INTO predictions (
            portfolio_id, predicted_iq, model_name, model_version,
            classification, feedback_suggestions
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING prediction_id
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            model_version = f"{model_name}_v1"
            
            cursor.execute(query, (
                portfolio_id, 
                predicted_iq, 
                model_name, 
                model_version,
                classification,
                feedback if feedback else []
            ))
            prediction_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Predição salva: ID={prediction_id}, Portfolio={portfolio_id}, IQ={predicted_iq:.2f}")
            return prediction_id
        except Exception as e:
            logger.error(f"❌ Erro ao salvar predição: {e}")
            return None
