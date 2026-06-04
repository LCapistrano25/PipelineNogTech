import luigi
import pandas as pd

class ExtractTransactionsNogTech(luigi.Task):
    def run(self):
        transactions_df = pd.read_csv(r"databases\transacoes_nogtech.csv", encoding="latin-1", delimiter=";")
        transactions_df.to_parquet(self.output().path)

    def output(self):
        return luigi.LocalTarget("output/loaded/transactions_nogtech.parquet")
