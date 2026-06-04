import logging
import os

import luigi
import pandas as pd

from config import settings
from infrastructure.utils.file_utils import save_df_to_parquet

logger = logging.getLogger(__name__)

class ExtractEngagementTask(luigi.Task):
    """
    Task para extrair dados de engajamento de alunos do arquivo JSON.
    """
    input_path = luigi.Parameter(default=settings.RAW_ENGAGEMENT_PATH)
    output_path = luigi.Parameter(default=settings.LOADED_ENGAGEMENT)

    def run(self) -> None:
        try:
            if not os.path.exists(str(self.input_path)):
                raise FileNotFoundError(f"Arquivo de entrada não encontrado: {self.input_path}")

            logger.info(f"Iniciando extração de engajamento de {self.input_path}")
            
            engagement_df = pd.read_json(str(self.input_path))
            
            if engagement_df.empty:
                logger.warning(f"O arquivo {self.input_path} está vazio.")
            else:
                logger.info(f"Extraídos {len(engagement_df)} registros.")
            
            save_df_to_parquet(engagement_df, self.output().path)
            
        except Exception as e:
            logger.error(f"Erro na extração de engajamento: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
