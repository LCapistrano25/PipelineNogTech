import luigi
import pandas as pd


from utils.format_date import parse_date
from utils.format_cpf import format_cpf
from utils.format_float import format_float

from pipeline.transform.transform_transactions import TransformTransactionsNogTech
from pipeline.transform.transform_engagaments import TransformEngagementNogTech


class TransformLeftJoinEngagementTrasactionsNogTech(luigi.Task):

    def requires(self):
        return [TransformTransactionsNogTech(), TransformEngagementNogTech()]

    def run(self):
        transactions_df = pd.read_parquet(self.input()[0].path)
        engagement_df = pd.read_parquet(self.input()[1].path)

        final_df = pd.merge(
            transactions_df, 
            engagement_df, 
            on=['cpf_aluno', 'mes', 'ano'], 
            how='left'
        )

        final_df.to_parquet(self.output().path, index=False)

    def output(self):
        return luigi.LocalTarget("output/transformed/left_join_engagement_transactions.parquet")