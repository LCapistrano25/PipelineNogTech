from datetime import datetime
from typing import Any, Optional

import pandas as pd

FORMATS = [
    '%Y%m%d',
    '%Y-%m-%d',
    '%d/%m/%Y',
    '%d-%m-%Y',
    '%Y-%m'
]

def parse_date(value: Any) -> Optional[datetime]:
    """
    Tenta converter uma string ou valor em um objeto datetime baseado em múltiplos formatos.
    
    Args:
        value: Valor da data.
        
    Returns:
        Objeto datetime ou None se não for possível converter.
    """
    if pd.isna(value):
        return None

    value_str = str(value).strip()

    for fmt in FORMATS:
        try:
            return datetime.strptime(value_str, fmt)
        except ValueError:
            continue
    
    try:
        dt = pd.to_datetime(value_str)
        return dt.to_pydatetime() if hasattr(dt, 'to_pydatetime') else dt
    except:
        return None
