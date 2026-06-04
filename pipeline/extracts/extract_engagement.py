import luigi
import pandas as pd

class ExtractEngagementNogTech(luigi.Task):
    def run(self):
        engagement_df = pd.read_json(r"databases\engajamento_alunos.json")
        engagement_df.to_parquet(self.output().path)

    def output(self):
        return luigi.LocalTarget("output/loaded/engagement_stundents.parquet")
