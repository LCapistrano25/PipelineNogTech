import logging
import os

import luigi
import pandas as pd

from config import settings
from infrastructure.utils.format_cpf import format_cpf
from infrastructure.utils.format_float import format_float
from pipelines.extract.extract_engagement import ExtractEngagementTask

logger = logging.getLogger(__name__)

class TransformEngagementTask(luigi.Task):
    """
    Task para transformar os dados de engajamento dos alunos.
    """
    output_path = luigi.Parameter(default=settings.PROCESSED_ENGAGEMENT)

    def requires(self):
        return [ExtractEngagementTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando transformação de engajamento")
            
            engagement_df = pd.read_parquet(self.input()[0].path)

            if engagement_df.empty:
                logger.warning("DataFrame de engajamento está vazio. Pulando transformações.")
                engagement_df.to_parquet(self.output().path, index=False)
                return

            # Transformações de data
            engagement_df['mes_referencia'] = pd.to_datetime(engagement_df['mes_referencia'], format='%Y-%m')
            engagement_df['mes'] = engagement_df['mes_referencia'].dt.month
            engagement_df['ano'] = engagement_df['mes_referencia'].dt.year
            
            # Formatações numéricas e strings
            engagement_df['horas_assistidas'] = engagement_df['horas_assistidas'].apply(format_float)
            engagement_df['nps_score'] = engagement_df['nps_score'].apply(format_float)
            engagement_df['cpf_aluno'] = engagement_df['cpf_aluno'].apply(format_cpf)
            
            logger.info(f"Transformados {len(engagement_df)} registros de engajamento.")

            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            engagement_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados transformados salvos em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na transformação de engajamento: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
