import luigi
import pandas as pd
from utils.format_date import parse_date
from utils.format_cpf import format_cpf
from utils.format_float import format_float
from utils.format_cep import format_cep

from pipeline.extracts.extract_transactions import ExtractTransactionsNogTech

class TransformTransactionsNogTech(luigi.Task):

    def requires(self):
        return [ExtractTransactionsNogTech()]

    def run(self):
        transactions_df = pd.read_parquet(self.input()[0].path)

        transactions_df['data_transacao'] = transactions_df['data_transacao'].apply(parse_date)
        transactions_df['mes'] = transactions_df['data_transacao'].dt.month
        transactions_df['ano'] = transactions_df['data_transacao'].dt.year
        
        transactions_df['cpf_aluno'] = transactions_df['cpf_aluno'].apply(format_cpf)
        transactions_df['valor_brl'] = transactions_df['valor_brl'].apply(format_float)
        transactions_df['cep_cobranca'] = transactions_df['cep_cobranca'].apply(format_cep)

        map_plans = (
            transactions_df.loc[
                transactions_df['plano_adquirido'].notna(),
                ['plano_adquirido', 'valor_brl']
            ]
            .drop_duplicates()
            .set_index('valor_brl')['plano_adquirido']
            .to_dict()
        )


        transactions_df['plano_adquirido'] = transactions_df['valor_brl'].apply(lambda x: map_plans.get(x, None))
        transactions_df['cep_cobranca'] = transactions_df['cep_cobranca'].apply(format_cep)

        transactions_df.to_parquet(self.output().path, index=False)

    def output(self):
        return luigi.LocalTarget('output/processed/transactions.parquet')