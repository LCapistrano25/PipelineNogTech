import logging
from typing import Optional

import requests

from infrastructure.services.holidays.iholiday_service import IHolidayService
from shared.responses.response_holiday import HolidayResponse

# Configuração básica de logging
logger = logging.getLogger(__name__)

class BrasilAPIHolidayService(IHolidayService):
    """
    Serviço para interação com a BrasilAPI para consulta de feriados.
    """
    BASE_URL = "https://brasilapi.com.br/api/feriados/v1/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

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
            response = requests.get(url, timeout=self.timeout)
            
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