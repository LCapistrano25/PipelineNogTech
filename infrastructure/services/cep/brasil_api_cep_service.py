import logging
from typing import Optional

import requests

from infrastructure.services.cep.icep_service import ICepService
from shared.responses.response_cep import CepResponse

# Configuração básica de logging
logger = logging.getLogger(__name__)

class BrasilAPICepService(ICepService):
    """
    Serviço para interação com a BrasilAPI para consulta de CEP.
    """
    BASE_URL = "https://brasilapi.com.br/api/cep/v2/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_cep(self, cep: str) -> Optional[CepResponse]:
        """
        Consulta um CEP na BrasilAPI e retorna um objeto CepResponse.
        
        Args:
            cep: O CEP a ser consultado (apenas números ou formatado).
            
        Returns:
            Um objeto CepResponse ou None se ocorrer um erro.
        """
        url = f"{self.BASE_URL}{cep}"
        try:
            logger.info(f"Consultando CEP: {cep}")
            response = requests.get(url, timeout=self.timeout)
            
            response.raise_for_status()
            
            data = response.json()
            return CepResponse(**data)
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao consultar CEP {cep}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao consultar CEP {cep}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar CEP {cep}: {e}")
            
        return None