import re
from typing import Any, Optional

def format_cpf(cpf: Any) -> Optional[str]:
    """
    Formata o CPF para o padrão 000.000.000-00.
    
    Args:
        cpf: Valor do CPF (string, int).
        
    Returns:
        CPF formatado ou None se o valor for inválido ou nulo.
    """
    if cpf is None:
        return None
        
    cpf_digits = re.sub(r'\D', '', str(cpf))

    if len(cpf_digits) != 11:
        return None

    return f'{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:]}'
