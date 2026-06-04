import logging
import os

import luigi
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)

class ExtractTransactionsTask(luigi.Task):
    """
    Task para extrair dados de transações do arquivo CSV.
    """
    input_path = luigi.Parameter(default=settings.RAW_TRANSACTIONS_PATH)
    output_path = luigi.Parameter(default=settings.LOADED_TRANSACTIONS)

    def run(self) -> None:
        try:
            if not os.path.exists(str(self.input_path)):
                raise FileNotFoundError(f"Arquivo de entrada não encontrado: {self.input_path}")

            logger.info(f"Iniciando extração de transações de {self.input_path}")
            
            transactions_df = pd.read_csv(
                str(self.input_path), 
                encoding="latin-1", 
                delimiter=";"
            )
            
            # Validação básica de dados
            if transactions_df.empty:
                logger.warning(f"O arquivo {self.input_path} está vazio.")
            else:
                logger.info(f"Extraídas {len(transactions_df)} transações.")
            
            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            transactions_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados salvos com sucesso em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na extração de transações: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
