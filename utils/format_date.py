
import pandas as pd

from datetime import datetime

FORMATS = [
    '%Y%m%d',
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%Y-%m'
]

def parse_date(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    for fmt in FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    
    # Se nenhum formato funcionar, tenta o pd.to_datetime como fallback
    try:
        return pd.to_datetime(value)
    except:
        return None
