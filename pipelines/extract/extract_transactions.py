import logging
import luigi
import pandas as pd
import os

# Configuração de logging
logger = logging.getLogger(__name__)

class ExtractTransactionsTask(luigi.Task):
    """
    Task para extrair dados de transações do arquivo CSV.
    """
    input_path = luigi.Parameter(default="databases/transacoes_nogtech.csv")
    output_path = luigi.Parameter(default="output/loaded/transactions_nogtech.parquet")

    def run(self) -> None:
        try:
            logger.info(f"Iniciando extração de transações de {self.input_path}")
            
            # Extração (Tratando encoding e delimitador)
            transactions_df = pd.read_csv(
                self.input_path, 
                encoding="latin-1", 
                delimiter=";"
            )
            
            logger.info(f"Extraídas {len(transactions_df)} transações.")
            
            # Garantir diretório de saída
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            
            # Salvando em Parquet
            transactions_df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados salvos com sucesso em {self.output_path}")
            
        except Exception as e:
            logger.error(f"Erro na extração de transações: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
