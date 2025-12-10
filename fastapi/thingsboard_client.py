"""
Cliente ThingsBoard para HubFólio
Envia dados de predições e métricas para visualização no dashboard
"""
import os
import logging
import json
import requests
from typing import Dict, Optional, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThingsBoardClient:
    """Cliente para enviar dados ao ThingsBoard"""
    
    def __init__(self):
        self.tb_url = os.getenv('THINGSBOARD_URL', 'http://thingsboard:9090')
        self.username = os.getenv('THINGSBOARD_USERNAME', 'tenant@thingsboard.org')
        self.password = os.getenv('THINGSBOARD_PASSWORD', 'tenant')
        self.device_token = os.getenv('THINGSBOARD_DEVICE_TOKEN', None)
        
        self.access_token = None
        self.device_id = None
        
        # Tentar autenticar se credenciais estiverem disponíveis
        if self.username and self.password:
            self._authenticate()
        
        logger.info(f"ThingsBoard Client initialized - URL: {self.tb_url}")
    
    def _authenticate(self) -> bool:
        """Autentica no ThingsBoard e obtém token"""
        try:
            auth_url = f"{self.tb_url}/api/auth/login"
            payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = requests.post(
                auth_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                self.access_token = response.json().get('token')
                logger.info("✅ Autenticado no ThingsBoard")
                return True
            else:
                logger.warning(f"⚠️ Falha na autenticação ThingsBoard: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao autenticar no ThingsBoard: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Verifica se a conexão com ThingsBoard está OK"""
        try:
            response = requests.get(f"{self.tb_url}/api/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ ThingsBoard não acessível: {e}")
            return False
    
    def send_telemetry(
        self,
        device_token: str,
        telemetry_data: Dict,
        timestamp: Optional[int] = None
    ) -> bool:
        """
        Envia dados de telemetria para o ThingsBoard
        
        Args:
            device_token: Token do dispositivo no ThingsBoard
            telemetry_data: Dicionário com dados de telemetria
            timestamp: Timestamp em milissegundos (opcional)
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            url = f"{self.tb_url}/api/v1/{device_token}/telemetry"
            
            # Adicionar timestamp se fornecido
            if timestamp:
                telemetry_data['ts'] = timestamp
            else:
                telemetry_data['ts'] = int(datetime.utcnow().timestamp() * 1000)
            
            response = requests.post(
                url,
                json=telemetry_data,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Telemetria enviada para ThingsBoard: {telemetry_data}")
                return True
            else:
                logger.warning(f"⚠️ Erro ao enviar telemetria: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao enviar telemetria para ThingsBoard: {e}")
            return False
    
    def send_prediction_data(
        self,
        device_token: str,
        prediction_data: Dict
    ) -> bool:
        """
        Envia dados de predição para o ThingsBoard
        
        Args:
            device_token: Token do dispositivo
            prediction_data: Dados da predição contendo:
                - portfolio_id
                - predicted_iq
                - classification
                - model_name
                - user_id (opcional)
                
        Returns:
            True se sucesso, False caso contrário
        """
        telemetry = {
            'predicted_iq': prediction_data.get('predicted_iq', 0),
            'portfolio_id': prediction_data.get('portfolio_id'),
            'model_name': prediction_data.get('model_name', 'unknown'),
            'classification': prediction_data.get('classification', 'unknown')
        }
        
        # Adicionar campos opcionais
        if 'user_id' in prediction_data:
            telemetry['user_id'] = prediction_data['user_id']
        
        if 'prediction_id' in prediction_data:
            telemetry['prediction_id'] = prediction_data['prediction_id']
        
        return self.send_telemetry(device_token, telemetry)
    
    def send_portfolio_metrics(
        self,
        device_token: str,
        metrics_data: Dict
    ) -> bool:
        """
        Envia métricas de portfólio para o ThingsBoard
        
        Args:
            device_token: Token do dispositivo
            metrics_data: Dados das métricas contendo:
                - portfolio_id
                - indice_qualidade
                - completude
                - clareza
                - consistencia_visual
                
        Returns:
            True se sucesso, False caso contrário
        """
        telemetry = {
            'portfolio_id': metrics_data.get('portfolio_id'),
            'indice_qualidade': metrics_data.get('indice_qualidade', 0),
            'completude': metrics_data.get('completude', 0),
            'clareza': metrics_data.get('clareza', 0),
            'consistencia_visual': metrics_data.get('consistencia_visual', 0)
        }
        
        return self.send_telemetry(device_token, telemetry)
    
    def send_batch_telemetry(
        self,
        device_token: str,
        telemetry_list: List[Dict]
    ) -> bool:
        """
        Envia múltiplos pontos de telemetria de uma vez
        
        Args:
            device_token: Token do dispositivo
            telemetry_list: Lista de dicionários com dados de telemetria
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            url = f"{self.tb_url}/api/v1/{device_token}/telemetry"
            
            # Formatar dados para batch
            batch_data = []
            for telemetry in telemetry_list:
                if 'ts' not in telemetry:
                    telemetry['ts'] = int(datetime.utcnow().timestamp() * 1000)
                batch_data.append(telemetry)
            
            response = requests.post(
                url,
                json=batch_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Batch de {len(batch_data)} pontos enviado para ThingsBoard")
                return True
            else:
                logger.warning(f"⚠️ Erro ao enviar batch: {response.status_code}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao enviar batch para ThingsBoard: {e}")
            return False

