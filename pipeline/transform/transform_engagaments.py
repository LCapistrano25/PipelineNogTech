import luigi
import pandas as pd
from utils.format_date import parse_date
from utils.format_cpf import format_cpf
from utils.format_float import format_float
from utils.format_cep import format_cep

from pipeline.extracts.extract_engagement import ExtractEngagementNogTech

class TransformEngagementNogTech(luigi.Task):

    def requires(self):
        return [ExtractEngagementNogTech()]

    def run(self):
        engagement_df = pd.read_parquet(self.input()[0].path)

        engagement_df['mes_referencia'] = pd.to_datetime(engagement_df['mes_referencia'], format='%Y-%m')
        engagement_df['mes'] = engagement_df['mes_referencia'].dt.month
        engagement_df['ano'] = engagement_df['mes_referencia'].dt.year
        engagement_df['horas_assistidas'] = engagement_df['horas_assistidas'].apply(format_float)
        engagement_df['nps_score'] = engagement_df['nps_score'].apply(format_float)

        engagement_df['cpf_aluno'] = engagement_df['cpf_aluno'].apply(format_cpf)
        engagement_df.to_parquet(self.output().path, index=False)

    def output(self):
        return luigi.LocalTarget('output/processed/engagement.parquet')
