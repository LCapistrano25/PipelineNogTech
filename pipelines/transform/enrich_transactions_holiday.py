import logging

import luigi
import pandas as pd

from config import settings
from infrastructure.services.holidays.holiday_enrichment_service import (
    HolidayEnrichmentService,
)
from infrastructure.utils.file_utils import save_df_to_parquet
from pipelines.transform.enrich_transactions_address import (
    EnrichTransactionsAddressTask,
)

logger = logging.getLogger(__name__)

class EnrichTransactionsHolidayTask(luigi.Task):
    """
    Task de Enriquecimento: Identifica se a transação ocorreu em um feriado nacional.
    Utiliza Cache persistente para otimização das consultas à BrasilAPI.
    """
    input_path = luigi.Parameter(default=settings.ENRICHED_ADDRESS)
    output_path = luigi.Parameter(default=settings.ENRICHED_HOLIDAY)

    def requires(self):
        return [EnrichTransactionsAddressTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando enriquecimento de feriados com estratégia de Cache")
            
            df = pd.read_parquet(self.input()[0].path)
            
            if df.empty:
                logger.warning("DataFrame de transações está vazio. Pulando enriquecimento de feriados.")
                save_df_to_parquet(df, self.output().path)
                return

            if 'data_transacao' not in df.columns:
                logger.error("Coluna 'data_transacao' não encontrada para verificar feriados.")
                save_df_to_parquet(df, self.output().path)
                return
            
            enrichment_service = HolidayEnrichmentService()
            df = enrichment_service.enrich_dataframe(df, 'data_transacao')

            save_df_to_parquet(df, self.output().path)
        
        except Exception as e:
            logger.error(f"Erro no enriquecimento de feriados: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
