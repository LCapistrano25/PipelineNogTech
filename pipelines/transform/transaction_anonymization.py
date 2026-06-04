import logging

import luigi
import pandas as pd

from config import settings
from infrastructure.utils.anonymization_utils import anonymize_transactions
from infrastructure.utils.file_utils import save_df_to_parquet
from pipelines.transform.transform_engagement_transactions import (
    TransformEnrichedDataTask,
)

logger = logging.getLogger(__name__)

class TransactionAnonymizationTask(luigi.Task):
    """
    Task de Transformação: Aplica regras de anonimização (LGPD) nos dados finais.
    Remove identificadores diretos e mascara dados sensíveis.
    """
    output_path = luigi.Parameter(default=settings.PROCESSED_ANONYMIZED)

    def requires(self):
        return [TransformEnrichedDataTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando anonimização de dados (LGPD)")
            
            df = pd.read_parquet(self.input()[0].path)
            
            if df.empty:
                logger.warning("DataFrame vazio. Pulando anonimização.")
                save_df_to_parquet(df, self.output().path)
                return

            # Aplica as regras de anonimização
            anonymized_df = anonymize_transactions(df)

            # Salva o resultado intermediário anonimizado
            save_df_to_parquet(anonymized_df, self.output().path)
            logger.info(f"Dados anonimizados salvos em {self.output_path}")

        except Exception as e:
            logger.error(f"Erro na anonimização de transações: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
