import logging
import luigi
import pandas as pd
import os
from config import settings

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
            
            # Validação básica de dados
            if engagement_df.empty:
                logger.warning(f"O arquivo {self.input_path} está vazio.")
            else:
                logger.info(f"Extraídos {len(engagement_df)} registros.")
            
            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            engagement_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados salvos com sucesso em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na extração de engajamento: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
