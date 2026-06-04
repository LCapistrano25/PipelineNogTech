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

            enrichment_service = CepEnrichmentService()
            df = enrichment_service.enrich_dataframe(df, 'cep_cobranca')

            save_df_to_parquet(df, self.output().path)
            
        except Exception as e:
            logger.error(f"Erro no enriquecimento de endereço: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
