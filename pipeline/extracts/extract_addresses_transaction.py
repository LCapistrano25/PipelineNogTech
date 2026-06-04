import luigi

import pandas as pd

from main import transactions_df
from pipeline.extracts.extract_transactions import ExtractTransactionsNogTech
from api.api_brasil.api_cep import APIBrasilRequestCep

class ExtractAddressesTransaction(luigi.Task):
    def requires(self):
        return ExtractTransactionsNogTech()

    def run(self):
        transactions_df = self.input().load()

        for _, row in transactions_df.iterrows():
            cep = row['cep']
            api = APIBrasilRequestCep(cep)
            response = api.get_cep()
            print(response)
    
    def output(self):
        return luigi.LocalTarget('output/extract/addresses.csv')