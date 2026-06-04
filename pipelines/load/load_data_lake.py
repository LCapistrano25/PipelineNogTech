import logging
import luigi
import pandas as pd
from config import settings
from infrastructure.utils.file_utils import save_df_to_parquet
from pipelines.transform.transaction_anonymization import TransactionAnonymizationTask

logger = logging.getLogger(__name__)

class LoadDataLakeTask(luigi.Task):
    """
    Task de Carga (Load): Finaliza o pipeline salvando os dados no Data Lake.
    Os dados são persistidos em formato Parquet e particionados por ano/mês.
    """
    output_path = luigi.Parameter(default=settings.ANONYMIZED_TRANSACTIONS)

    def requires(self):
        return [TransactionAnonymizationTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando a carga final no Data Lake")
            
            # Lê os dados anonimizados da task anterior
            df = pd.read_parquet(self.input()[0].path)
            
            if df.empty:
                logger.warning("Nenhum dado para carregar no Data Lake.")
                save_df_to_parquet(df, self.output().path)
                return

            # Realiza a carga particionada (Requisito 🟥 Load - Opção B)
            save_df_to_parquet(
                df, 
                self.output().path, 
                partition_cols=['ano', 'mes']
            )
            
            logger.info(f"Carga final concluída com sucesso em {self.output_path}")

        except Exception as e:
            logger.error(f"Erro na carga do Data Lake: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        # No Data Lake particionado, o target é o diretório raiz
        return luigi.LocalTarget(str(self.output_path))
