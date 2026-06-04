import logging
import os
from typing import Any, Dict

import luigi
import pandas as pd

from config import settings
from infrastructure.cache.address_cache import AddressCache
from infrastructure.services.cep.brasil_api_cep_service import BrasilAPICepService
from pipelines.transform.transform_transactions import TransformTransactionsTask

logger = logging.getLogger(__name__)

class EnrichTransactionsAddressTask(luigi.Task):
    """
    Task de Enriquecimento: Consulta a BrasilAPI para buscar detalhes do endereço,
    utilizando uma camada de Cache persistente para otimização.
    """
    output_path = luigi.Parameter(default=settings.ENRICHED_ADDRESS)

    def requires(self):
        return [TransformTransactionsTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando enriquecimento de endereço com estratégia de Cache")
            
            df = pd.read_parquet(self.input()[0].path)
            
            if df.empty:
                logger.warning("DataFrame de transações está vazio. Pulando enriquecimento de endereço.")
                df.to_parquet(self.output().path, index=False)
                return

            unique_ceps = df['cep_cobranca'].dropna().unique()
            
            api_service = BrasilAPICepService(timeout=settings.API_TIMEOUT)
            cache = AddressCache(cache_file=settings.CEP_CACHE_PATH)
            
            address_map: Dict[str, Dict[str, Any]] = {}
            new_queries = 0
            cached_hits = 0

            for cep in unique_ceps:
                cached_result = cache.get(str(cep))
                
                if cached_result:
                    address_map[str(cep)] = cached_result
                    cached_hits += 1
                else:
                    result = api_service.get_cep(str(cep))
                    if result:
                        address_data = {
                            'bairro': result.neighborhood,
                            'cidade': result.city,
                            'estado': result.state
                        }
                        address_map[str(cep)] = address_data
                        cache.set(str(cep), address_data)
                        new_queries += 1

            logger.info(f"Enriquecimento concluído. Cache Hits: {cached_hits}, Novas Consultas: {new_queries}")

            enriched_df = df.copy()
            for col in ['bairro', 'cidade', 'estado']:
                enriched_df[col] = enriched_df['cep_cobranca'].astype(str).map(lambda x: address_map.get(x, {}).get(col))

            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            enriched_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados enriquecidos com endereço salvos em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro no enriquecimento de endereço: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
