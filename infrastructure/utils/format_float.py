
from typing import Any, Optional

import pandas as pd

def format_float(value: Any) -> Optional[float]:
    """
    Converte uma string formatada em real (ex: '49,90' ou '1.234,56') para float.
    Retorna None se o valor for inválido ou nulo.
    """
    if pd.isna(value) or str(value).strip() == "":
        return None

    try:
        if isinstance(value, str):
            clean_value = value.replace('.', '').replace(',', '.')
            return float(clean_value)
        return float(value)
    except (ValueError, TypeError):
        return None
