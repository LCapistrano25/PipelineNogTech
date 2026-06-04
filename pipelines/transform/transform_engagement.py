import logging
import luigi
import pandas as pd
import os
from infrastructure.utils.format_cpf import format_cpf
from infrastructure.utils.format_float import format_float
from pipelines.extract.extract_engagement import ExtractEngagementTask

# Configuração de logging
logger = logging.getLogger(__name__)

class TransformEngagementTask(luigi.Task):
    """
    Task para transformar os dados de engajamento dos alunos.
    """
    output_path = luigi.Parameter(default='output/processed/engagement.parquet')

    def requires(self):
        return [ExtractEngagementTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando transformação de engajamento")
            
            # Leitura do input (resultado da task anterior)
            engagement_df = pd.read_parquet(self.input()[0].path)

            # Transformações de data
            engagement_df['mes_referencia'] = pd.to_datetime(engagement_df['mes_referencia'], format='%Y-%m')
            engagement_df['mes'] = engagement_df['mes_referencia'].dt.month
            engagement_df['ano'] = engagement_df['mes_referencia'].dt.year
            
            # Formatações numéricas e strings
            engagement_df['horas_assistidas'] = engagement_df['horas_assistidas'].apply(format_float)
            engagement_df['nps_score'] = engagement_df['nps_score'].apply(format_float)
            engagement_df['cpf_aluno'] = engagement_df['cpf_aluno'].apply(format_cpf)
            
            # Log de progresso
            logger.info(f"Transformados {len(engagement_df)} registros de engajamento.")

            # Garantir diretório de saída
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Salvando o resultado processado
            engagement_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados transformados salvos em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na transformação de engajamento: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
