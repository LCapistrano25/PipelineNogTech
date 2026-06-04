from typing import Optional
from abc import ABC, abstractmethod
from shared.responses.response_cep import CepResponse

class ICepService(ABC):
    """
    Serviço para interação com a BrasilAPI para consulta de CEP.
    """
    
    @abstractmethod
    def get_cep(self, cep: str) -> Optional[CepResponse]:
        """
        Consulta um CEP na BrasilAPI e retorna um objeto CepResponse.
        
        Args:
            cep: O CEP a ser consultado (apenas números ou formatado).
            
        Returns:
            Um objeto CepResponse ou None se ocorrer um erro.
        """
    ...