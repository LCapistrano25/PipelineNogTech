import os
import logging
import pandas as pd
from typing import Union

logger = logging.getLogger(__name__)

def ensure_dir(file_path: str) -> None:
    """
    Garante que o diretório pai de um arquivo existe.
    """
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Diretório criado: {directory}")

def save_df_to_parquet(df: pd.DataFrame, file_path: Union[str, os.PathLike], index: bool = False) -> None:
    """
    Salva um DataFrame em formato Parquet, garantindo que o diretório de destino exista.
    """
    path_str = str(file_path)
    ensure_dir(path_str)
    df.to_parquet(path_str, index=index)
    logger.info(f"Dados salvos com sucesso em: {path_str}")
