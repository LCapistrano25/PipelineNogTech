from typing import Optional
from abc import ABC, abstractmethod
from shared.responses.response_holiday import HolidayResponse

class IHolidayService(ABC):
    """
    Serviço para interação com a BrasilAPI para consulta de feriados.
    """
  
    @abstractmethod
    def get_holiday(self, year: str) -> Optional[HolidayResponse]: 
        """
        Consulta feriados de um ano na BrasilAPI e retorna um objeto HolidayResponse.
        
        Args:
            year: O ano a ser consultado (apenas números).
            
        Returns:
            Uma lista de objetos HolidayResponse ou None se ocorrer um erro.
        """
    ...