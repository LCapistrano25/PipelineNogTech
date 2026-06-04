import re
from typing import Any, Optional

import pandas as pd

def format_cep(cep: Any) -> Optional[str]:
    """
    Formata um CEP para o padrão 99999-999.

    Regras:
    - Remove caracteres não numéricos.
    - Mantém apenas os 8 primeiros dígitos.
    - Retorna None para valores nulos ou CEPs inválidos.

    Args:
        cep: Valor do CEP (string, int, float, etc.).

    Returns:
        CEP formatado (99999-999) ou None.
    """
    if pd.isna(cep):
        return None

    digits = re.sub(r"\D", "", str(cep))

    digits = digits[:8]

    if len(digits) != 8:
        return None

    return f"{digits[:5]}-{digits[5:]}"