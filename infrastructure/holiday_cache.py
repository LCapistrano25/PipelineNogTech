import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class HolidayCache:
    """
    Sistema de cache persistente para feriados consultados via ano.
    Evita chamadas desnecessárias à API e economiza recursos.
    """
    def __init__(self, cache_file: str = "databases/holiday_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Carrega o cache do arquivo JSON se existir."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar cache de feriados: {e}")
        return {}

    def _save_cache(self) -> None:
        """Salva o estado atual do cache no arquivo JSON."""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache de feriados: {e}")

    def get(self, year: str, default: Any = None) -> Optional[Dict[str, Any]]:
        """Busca um feriados no cache pelo ano."""
        return self.cache.get(year, default)

    def set(self, year: str, holiday_data: Dict[str, Any]) -> None:
        """Adiciona um feriados ao cache e persiste no disco."""
        self.cache[year] = holiday_data
        self._save_cache()
