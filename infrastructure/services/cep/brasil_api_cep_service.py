import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from shared.responses.response_cep import CepResponse

# Configuração básica de logging
logger = logging.getLogger(__name__)

class BrasilAPICepService:
    """
    Serviço para interação com a BrasilAPI para consulta de CEP.
    """
    BASE_URL = "https://brasilapi.com.br/api/cep/v2/"

    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.session = requests.Session()
        
        # Configuração de Retry automático (Requisito de Resiliência)
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

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
            response = self.session.get(url, timeout=self.timeout)
            
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