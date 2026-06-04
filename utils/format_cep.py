import re
import pandas as pd


def format_cep(cep) -> str:
    """
    Formatar CEP
    """
    if pd.isna(cep):
        return None

    cep = str(cep)

    return re.sub(r'\D', '', cep)