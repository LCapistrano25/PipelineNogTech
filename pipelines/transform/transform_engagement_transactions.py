import logging
import luigi
import pandas as pd
import os
from config import settings
from pipelines.transform.enrich_transactions_holiday import EnrichTransactionsHolidayTask
from pipelines.transform.transform_engagement import TransformEngagementTask

logger = logging.getLogger(__name__)

class TransformEnrichedDataTask(luigi.Task):
    """
    Task Final: Realiza o join entre transações enriquecidas e engajamento dos alunos.
    Gera o dataset consolidado para análise.
    """
    output_path = luigi.Parameter(default=settings.FINAL_ENRICHED_DATA)

    def requires(self):
        return [EnrichTransactionsHolidayTask(), TransformEngagementTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando join final de transações e engajamento")
            
            transactions_df = pd.read_parquet(self.input()[0].path)
            engagement_df = pd.read_parquet(self.input()[1].path)

            if transactions_df.empty:
                logger.error("DataFrame de transações está vazio. O resultado final será parcial ou vazio.")
            
            # Join dos dados
            final_df = pd.merge(
                transactions_df, 
                engagement_df, 
                on=['cpf_aluno', 'mes', 'ano'], 
                how='left'
            )

            # Validação pós-join
            if not final_df.empty:
                logger.info(f"Join concluído. Dataset final com {len(final_df)} registros.")
                # Verifica se houve correspondência de engajamento
                matched_engagement = final_df['horas_assistidas'].notna().sum()
                logger.info(f"Registros com dados de engajamento correspondentes: {matched_engagement}")
            else:
                logger.warning("O join resultou em um dataset vazio.")

            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            final_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dataset final consolidado salvo em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro no join final de dados: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
