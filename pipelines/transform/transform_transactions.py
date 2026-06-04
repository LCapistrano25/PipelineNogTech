import logging
import os

import luigi
import pandas as pd

from config import settings
from infrastructure.utils.file_utils import save_df_to_parquet
from infrastructure.utils.format_cep import format_cep
from infrastructure.utils.format_cpf import format_cpf
from infrastructure.utils.format_date import parse_date
from infrastructure.utils.format_float import format_float
from pipelines.extract.extract_transactions import ExtractTransactionsTask

logger = logging.getLogger(__name__)

class TransformTransactionsTask(luigi.Task):
    """
    Task para transformar os dados de transações.
    """
    output_path = luigi.Parameter(default=settings.PROCESSED_TRANSACTIONS)

    def requires(self):
        return [ExtractTransactionsTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando transformação de transações")
            
            transactions_df = pd.read_parquet(self.input()[0].path)

            if transactions_df.empty:
                logger.warning("DataFrame de transações está vazio. Pulando transformações.")
                save_df_to_parquet(transactions_df, self.output().path)
                return

            # Transformações de data
            transactions_df['data_transacao'] = transactions_df['data_transacao'].apply(parse_date)
            transactions_df['mes'] = transactions_df['data_transacao'].dt.month
            transactions_df['ano'] = transactions_df['data_transacao'].dt.year
            
            # Formatações de strings e números
            transactions_df['cpf_aluno'] = transactions_df['cpf_aluno'].apply(format_cpf)
            transactions_df['valor_brl'] = transactions_df['valor_brl'].apply(format_float)
            transactions_df['cep_cobranca'] = transactions_df['cep_cobranca'].apply(format_cep)

            # Mapeamento de planos baseado no valor (Lógica de negócio)
            map_plans = (
                transactions_df.loc[
                    transactions_df['plano_adquirido'].notna(),
                    ['plano_adquirido', 'valor_brl']
                ]
                .drop_duplicates()
                .set_index('valor_brl')['plano_adquirido']
                .to_dict()
            )

            # Preenche planos nulos baseado no valor
            transactions_df['plano_adquirido'] = transactions_df['plano_adquirido'].fillna(transactions_df['valor_brl'].map(map_plans))

            logger.info(f"Transformadas {len(transactions_df)} transações.")
            save_df_to_parquet(transactions_df, self.output().path)
            
        except Exception as e:
            logger.error(f"Erro na transformação de transações: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
