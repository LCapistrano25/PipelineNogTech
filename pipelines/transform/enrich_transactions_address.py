import logging
import os
from typing import Any, Dict

import luigi
import pandas as pd

from config import settings
from infrastructure.services.cep.cep_enrichment_service import CepEnrichmentService
from infrastructure.utils.file_utils import save_df_to_parquet
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
                save_df_to_parquet(df, self.output().path)
                return

            unique_ceps = df['cep_cobranca'].dropna().unique()
            
            enrichment_service = CepEnrichmentService()
            address_map = enrichment_service.enrich_ceps(unique_ceps)

            enriched_df = df.copy()
            for col in ['bairro', 'cidade', 'estado']:
                enriched_df[col] = enriched_df['cep_cobranca'].astype(str).map(lambda x: address_map.get(x, {}).get(col))

            save_df_to_parquet(enriched_df, self.output().path)
            
        except Exception as e:
            logger.error(f"Erro no enriquecimento de endereço: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
