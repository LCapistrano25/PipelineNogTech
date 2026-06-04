import logging
import luigi
import pandas as pd
from typing import Any

# Configuração de logging
logger = logging.getLogger(__name__)

class ExtractEngagementTask(luigi.Task):
    """
    Task para extrair dados de engajamento de alunos do arquivo JSON.
    """
    input_path = luigi.Parameter(default="databases/engajamento_alunos.json")
    output_path = luigi.Parameter(default="output/loaded/engagement_students.parquet")

    def run(self) -> None:
        try:
            logger.info(f"Iniciando extração de engajamento de {self.input_path}")
            
            # Extração
            engagement_df = pd.read_json(self.input_path)
            
            # Log de progresso
            logger.info(f"Extraídos {len(engagement_df)} registros.")
            
            # Garantir diretório de saída
            import os
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Salvando em Parquet (Carga inicial)
            engagement_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados salvos com sucesso em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na extração de engajamento: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
