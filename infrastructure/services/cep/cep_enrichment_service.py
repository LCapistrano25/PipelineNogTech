import logging
from typing import Any, Dict, List, Set

from config import settings
from infrastructure.cache.address_cache import AddressCache
from infrastructure.services.cep.brasil_api_cep_service import BrasilAPICepService

logger = logging.getLogger(__name__)

class CepEnrichmentService:
    """
    Serviço de aplicação para orquestrar o enriquecimento de endereços via CEP,
    utilizando cache para otimização.
    """

    def __init__(self, timeout: int = settings.API_TIMEOUT, cache_path: str = settings.CEP_CACHE_PATH):
        self.api_service = BrasilAPICepService(timeout=timeout)
        self.cache = AddressCache(cache_file=cache_path)

    def enrich_ceps(self, ceps: List[Any]) -> Dict[str, Dict[str, Any]]:
        """
        Busca os endereços para uma lista de CEPs, utilizando o cache primeiro.
        
        Args:
            ceps: Lista de CEPs únicos.
            
        Returns:
            Um dicionário mapeando CEP para os dados de endereço.
        """
        address_map: Dict[str, Dict[str, Any]] = {}
        new_queries = 0
        cached_hits = 0

        # Garantir CEPs únicos e remover nulos
        unique_ceps: Set[str] = {str(cep) for cep in ceps if cep is not None and str(cep).strip() != ""}

        for cep in unique_ceps:
            cached_result = self.cache.get(cep)
            
            if cached_result:
                address_map[cep] = cached_result
                cached_hits += 1
            else:
                result = self.api_service.get_cep(cep)
                if result:
                    address_data = {
                        'bairro': result.neighborhood,
                        'cidade': result.city,
                        'estado': result.state
                    }
                    address_map[cep] = address_data
                    self.cache.set(cep, address_data)
                    new_queries += 1

        logger.info(f"Enriquecimento de CEP concluído. Cache Hits: {cached_hits}, Novas Consultas: {new_queries}")
        return address_map
