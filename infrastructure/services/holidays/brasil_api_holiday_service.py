import logging
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from shared.responses.response_holiday import HolidayResponse

# Configuração básica de logging
logger = logging.getLogger(__name__)

class BrasilAPIHolidayService:
    """
    Serviço para interação com a BrasilAPI para consulta de feriados.
    """
    BASE_URL = "https://brasilapi.com.br/api/feriados/v1/"

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

    def get_holiday(self, year: str) -> Optional[HolidayResponse]: 
        """
        Consulta feriados de um ano na BrasilAPI e retorna um objeto CepResponse.
        
        Args:
            year: O ano a ser consultado (apenas números).
            
        Returns:
            Uma lista de objetos HolidayResponse ou None se ocorrer um erro.
        """
        url = f"{self.BASE_URL}{year}"
        try:
            logger.info(f"Consultando ano: {year}")
            response = self.session.get(url, timeout=self.timeout)
            
            response.raise_for_status()
            
            data = response.json()
            return list(map(lambda x: HolidayResponse(**x), data))     
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erro HTTP ao consultar feriados {year}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão ao consultar feriados {year}: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado ao processar feriados {year}: {e}")
            
        return None