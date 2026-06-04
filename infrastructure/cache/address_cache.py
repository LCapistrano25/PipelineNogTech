import json
import logging
import os
from typing import Any, Dict, Optional

from infrastructure.cache.icache import ICache
from infrastructure.utils.file_utils import ensure_dir

logger = logging.getLogger(__name__)

class AddressCache(ICache):
    """
    Sistema de cache persistente para endereços consultados via CEP.
    Evita chamadas desnecessárias à API e economiza recursos.
    """
    def __init__(self, cache_file: str = "databases/cep_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        """Carrega o cache do arquivo JSON se existir."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar cache de CEP: {e}")
        return {}

    def _save_cache(self) -> None:
        """Salva o estado atual do cache no arquivo JSON."""
        try:
            ensure_dir(self.cache_file)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar cache de CEP: {e}")

    def get(self, cep: str, default: Any = None) -> Optional[Dict[str, Any]]:
        """Busca um endereço no cache pelo CEP."""
        return self.cache.get(cep, default)

    def set(self, cep: str, address_data: Dict[str, Any]) -> None:
        """Adiciona um endereço ao cache e persiste no disco."""
        self.cache[cep] = address_data
        self._save_cache()
