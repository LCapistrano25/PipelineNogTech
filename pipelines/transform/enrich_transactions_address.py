import logging
import luigi
import pandas as pd
import os
from typing import Dict, Any
from services.brasil_api_cep_service import BrasilAPICepService
from infrastructure.address_cache import AddressCache
from pipelines.transform.transform_transactions import TransformTransactionsTask
from infrastructure.utils.format_cep import format_cep

logger = logging.getLogger(__name__)

class EnrichTransactionsAddressTask(luigi.Task):
    """
    Task de Enriquecimento: Consulta a BrasilAPI para buscar detalhes do endereço,
    utilizando uma camada de Cache persistente para otimização.
    """
    output_path = luigi.Parameter(default='output/processed/transactions_enriched_address.parquet')

    def requires(self):
        return [TransformTransactionsTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando enriquecimento de endereço com estratégia de Cache")
            
            # Carrega dados transformados
            df = pd.read_parquet(self.input()[0].path)
            
            # Identifica CEPs únicos
            unique_ceps = df['cep_cobranca'].dropna().unique()
            
            # Inicializa Serviços
            api_service = BrasilAPICepService()
            cache = AddressCache()
            
            address_map: Dict[str, Dict[str, Any]] = {}
            new_queries = 0
            cached_hits = 0

            for cep in unique_ceps:
                # 1. Tenta buscar no Cache primeiro
                cached_result = cache.get(cep)
                print(cached_result)
                
                if cached_result:
                    address_map[cep] = cached_result
                    cached_hits += 1
                else:

                    formatted_cep = format_cep(cep)
                    if not formatted_cep:
                        continue
                    
                    # 2. Se não estiver no cache, consulta a API
                    result = api_service.get_cep(formatted_cep)
                    if result:
                        address_data = {
                            'bairro_cobranca': result.neighborhood,
                            'cidade_cobranca': result.city,
                            'estado_cobranca': result.state
                        }
                        address_map[cep] = address_data
                        # 3. Salva no Cache para futuras execuções
                        cache.set(cep, address_data)
                        new_queries += 1

            logger.info(f"Enriquecimento concluído. Cache Hits: {cached_hits}, Novas Consultas: {new_queries}")

            # 4. Mapeia os resultados de volta para o DataFrame
            enriched_df = df.copy()
            for col in ['bairro_cobranca', 'cidade_cobranca', 'estado_cobranca']:
                enriched_df[col] = enriched_df['cep_cobranca'].map(lambda x: address_map.get(x, {}).get(col))

            # 5. Salva o resultado
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            enriched_df.to_parquet(self.output().path, index=False)
            
        except Exception as e:
            logger.error(f"Erro no enriquecimento de CEP: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
