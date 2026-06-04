import logging
import os
from typing import Any, Dict, List

import luigi
import pandas as pd

from config import settings
from infrastructure.cache.holiday_cache import HolidayCache
from infrastructure.services.holidays.brasil_api_holiday_service import (
    BrasilAPIHolidayService,
)
from pipelines.transform.enrich_transactions_address import (
    EnrichTransactionsAddressTask,
)

logger = logging.getLogger(__name__)

class EnrichTransactionsHolidayTask(luigi.Task):
    """
    Task de Enriquecimento: Identifica se a transação ocorreu em um feriado nacional.
    Utiliza Cache persistente para otimização das consultas à BrasilAPI.
    """
    input_path = luigi.Parameter(default=settings.ENRICHED_ADDRESS)
    output_path = luigi.Parameter(default=settings.ENRICHED_HOLIDAY)

    def requires(self):
        return [EnrichTransactionsAddressTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando enriquecimento de feriados com estratégia de Cache")
            
            df = pd.read_parquet(self.input()[0].path)
            
            if df.empty:
                logger.warning("DataFrame de transações está vazio. Pulando enriquecimento de feriados.")
                df.to_parquet(self.output().path, index=False)
                return

            # Garante que a coluna de data é datetime
            if 'data_transacao' not in df.columns:
                logger.error("Coluna 'data_transacao' não encontrada para verificar feriados.")
                df.to_parquet(self.output().path, index=False)
                return
            
            df['data_transacao'] = pd.to_datetime(df['data_transacao'])
            years = df['data_transacao'].dt.year.dropna().unique()
            logger.info(f"Anos encontrados na coluna 'data_transacao': {years}")
            
            cache = HolidayCache(cache_file=settings.HOLIDAY_CACHE_PATH)
            holiday_service = BrasilAPIHolidayService(timeout=settings.API_TIMEOUT)

            # Mapa de feriados por ano: { "2024": [date1, date2, ...] }
            holiday_dates_by_year: Dict[str, List[str]] = {}

            for year in years:
                year_str = str(int(year))
                cached_holidays = cache.get(year_str)
                
                if cached_holidays:
                    # Extrai apenas as datas dos feriados salvos no cache
                    holiday_dates_by_year[year_str] = [h['date'] for h in cached_holidays]
                else:
                    logger.info(f"Consultando feriados para o ano {year_str}")
                    holiday_list = holiday_service.get_holiday(year_str)
                    
                    if holiday_list:
                        # Salva o objeto completo no cache para referência futura
                        holiday_data = [h.model_dump() for h in holiday_list]
                        cache.set(year_str, holiday_data)
                        
                        # Extrai apenas as datas para o processamento atual
                        holiday_dates_by_year[year_str] = [h['date'] for h in holiday_data]
                    else:
                        holiday_dates_by_year[year_str] = []

            # 4. Cria a coluna indicadora de feriado
            def check_is_holiday(row) -> bool:
                if pd.isna(row['data_transacao']):
                    return False
                
                dt_str = row['data_transacao'].strftime('%Y-%m-%d')
                year_str = str(row['data_transacao'].year)
                
                holidays = holiday_dates_by_year.get(year_str, [])
                return dt_str in holidays

            df['venda_em_feriado'] = df.apply(check_is_holiday, axis=1)
            
            logger.info(f"Enriquecimento de feriados concluído. {df['venda_em_feriado'].sum()} transações em feriados.")

            os.makedirs(os.path.dirname(str(self.output_path)), exist_ok=True)
            df.to_parquet(self.output().path, index=False)
            logger.info(f"Dados enriquecidos com feriados salvos em {self.output_path}")
        
        except Exception as e:
            logger.error(f"Erro no enriquecimento de feriados: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(str(self.output_path))
