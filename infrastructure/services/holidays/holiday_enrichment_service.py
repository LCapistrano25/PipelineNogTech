import logging
from typing import Any, Dict, List, Set

from config import settings
from infrastructure.cache.holiday_cache import HolidayCache
from infrastructure.services.holidays.brasil_api_holiday_service import (
    BrasilAPIHolidayService,
)

logger = logging.getLogger(__name__)

class HolidayEnrichmentService:
    """
    Serviço de aplicação para orquestrar o enriquecimento de feriados,
    utilizando cache para otimização.
    """

    def __init__(self, timeout: int = settings.API_TIMEOUT, cache_path: str = settings.HOLIDAY_CACHE_PATH):
        self.holiday_service = BrasilAPIHolidayService(timeout=timeout)
        self.cache = HolidayCache(cache_file=cache_path)

    def get_holidays_by_year(self, years: List[Any]) -> Dict[str, List[str]]:
        """
        Busca os feriados para uma lista de anos, utilizando o cache primeiro.
        
        Args:
            years: Lista de anos únicos.
            
        Returns:
            Um dicionário mapeando ano (string) para uma lista de datas de feriados (strings 'YYYY-MM-DD').
        """
        holiday_dates_by_year: Dict[str, List[str]] = {}
        
        # Garantir anos únicos e formatados como string
        unique_years: Set[str] = {str(int(year)) for year in years if year is not None and not isinstance(year, str) or (isinstance(year, str) and year.isdigit())}

        for year_str in unique_years:
            cached_holidays = self.cache.get(year_str)
            
            if cached_holidays:
                logger.debug(f"Cache hit para feriados do ano {year_str}")
                # No cache guardamos a lista de dicionários (HolidayResponse serializado)
                holiday_dates_by_year[year_str] = [h['date'] for h in cached_holidays]
            else:
                logger.info(f"Consultando feriados para o ano {year_str}")
                holiday_list = self.holiday_service.get_holiday(year_str)
                
                if holiday_list:
                    # Salva o objeto completo no cache para referência futura
                    holiday_data = [h.model_dump() for h in holiday_list]
                    self.cache.set(year_str, holiday_data)
                    
                    # Extrai apenas as datas para o processamento atual
                    holiday_dates_by_year[year_str] = [h['date'] for h in holiday_data]
                else:
                    holiday_dates_by_year[year_str] = []

        return holiday_dates_by_year
