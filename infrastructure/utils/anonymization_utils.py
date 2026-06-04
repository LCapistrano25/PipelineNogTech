import pandas as pd
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

def anonymize_cpf(cpf: Optional[str]) -> Optional[str]:
    """
    Anonimiza o CPF conforme a LGPD: ***.456.789-**
    Mantém apenas os 6 dígitos centrais visíveis.
    """
    if not cpf or not isinstance(cpf, str):
        return cpf
    
    # O CPF deve estar no formato 000.000.000-00 (conforme padronização prévia)
    if len(cpf) == 14:
        return f"***{cpf[3:12]}**"
    
    return cpf

def anonymize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica as regras de anonimização da LGPD no DataFrame de transações:
    1. Mascara o CPF (mantendo 6 dígitos centrais).
    2. Remove a coluna 'nome_aluno' completamente.
    """
    temp_df = df.copy()
    
    # 1. Anonimização de CPF
    if 'cpf_aluno' in temp_df.columns:
        temp_df['cpf_aluno'] = temp_df['cpf_aluno'].apply(anonymize_cpf)
        logger.info("CPF anonimizado com sucesso.")
    
    # 2. Remoção do nome do aluno
    if 'nome_aluno' in temp_df.columns:
        temp_df = temp_df.drop(columns=['nome_aluno'])
        logger.info("Coluna 'nome_aluno' removida para conformidade com LGPD.")
    
    return temp_df
