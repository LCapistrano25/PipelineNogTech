import logging
import requests
from typing import Optional
from domain.entities.response_cep import ResponseCep

# Configuração básica de logging
logger = logging.getLogger(__name__)

class BrasilAPIService:
    """
    Serviço para interação com a BrasilAPI para consulta de CEP.
    """
    BASE_URL = "https://brasilapi.com.br/api/cep/v2/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_cep(self, cep: str) -> Optional[ResponseCep]:
        """
        Consulta um CEP na BrasilAPI e retorna um objeto ResponseCep.
        
        Args:
            cep: O CEP a ser consultado (apenas números ou formatado).
            
        Returns:
            Um objeto ResponseCep ou None se ocorrer um erro.
        """
        url = f"{self.BASE_URL}{cep}"
        try:
            logger.info(f"Consultando CEP: {cep}")
            response = requests.get(url, timeout=self.timeout)
            
            response.raise_for_status()
            
            data = response.json()
            return ResponseCep(**data)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao consultar CEP {cep}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao consultar CEP {cep}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar CEP {cep}: {e}")
            
        return None