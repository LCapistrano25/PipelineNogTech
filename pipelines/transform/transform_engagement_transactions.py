import logging
import luigi
import pandas as pd
import os
from pipelines.transform.enrich_transactions_holiday import EnrichTransactionsHolidayTask
from pipelines.transform.transform_engagement import TransformEngagementTask

# Configuração de logging
logger = logging.getLogger(__name__)

class TransformEnrichedDataTask(luigi.Task):
    """
    Task para realizar o join entre transações e engajamento.
    Representa a etapa final de transformação (Enriched/Transformed).
    """
    output_path = luigi.Parameter(default="output/transformed/enriched_engagement_transactions.parquet")

    def requires(self):
        return [EnrichTransactionsHolidayTask(), TransformEngagementTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando join de transações e engajamento")
            
            # Leitura dos inputs processados
            transactions_df = pd.read_parquet(self.input()[0].path)
            engagement_df = pd.read_parquet(self.input()[1].path)

            # Join dos dados (Lógica de enriquecimento)
            final_df = pd.merge(
                transactions_df, 
                engagement_df, 
                on=['cpf_aluno', 'mes', 'ano'], 
                how='left'
            )

            logger.info(f"Join concluído. Total de registros: {len(final_df)}")

            # Garantir diretório de saída
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Salvando o resultado final
            final_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados enriquecidos salvos em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro no join de dados: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
