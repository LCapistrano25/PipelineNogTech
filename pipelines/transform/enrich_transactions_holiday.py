import logging
import luigi
import pandas as pd
from services.brasil_api_holiday_service import BrasilAPIHolidayService
from infrastructure.holiday_cache import HolidayCache
from pipelines.transform.enrich_transactions_address import EnrichTransactionsAddressTask

logger = logging.getLogger(__name__)

class EnrichTransactionsHolidayTask(luigi.Task):
    """
    Task de Enriquecimento: Consulta a BrasilAPI para buscar detalhes do feriados,
    utilizando uma camada de Cache persistente para otimização.
    """
    input_path = luigi.Parameter(default='output/processed/transactions_enriched_address.parquet')
    output_path = luigi.Parameter(default='output/processed/transactions_enriched_holiday.parquet')

    def requires(self):
        return [EnrichTransactionsAddressTask()]

    def run(self) -> None:
        try:
            logger.info("Iniciando enriquecimento de feriados com estratégia de Cache")
            
            # Carrega dados transformados
            df = pd.read_parquet(self.input()[0].path)
            
            # Identifica anos únicos
            years = df['ano'].dropna().unique()
            print(years)
            
            cache = HolidayCache()
            holiday_service = BrasilAPIHolidayService()

            holiday_map: Dict[str, Dict[str, Any]] = {}
            new_queries = 0
            cached_hits = 0

            for year in years:
                year_str = str(year)
                cache_results = cache.get(year_str, None)
                if cache_results:
                    holiday_map[year_str] = cache_results
                    cached_hits += 1
                else:
                    logger.info(f"Consultando feriados para o ano {year_str}")
                    holiday_searched = holiday_service.get_holiday(year_str)
                    
                    # Converte modelos Pydantic para dicts antes de salvar no cache
                    holiday_data = [h.model_dump() for h in holiday_searched] if holiday_searched else []
                    
                    holiday_map[year_str] = holiday_data
                    cache.set(year_str, holiday_data)
                    new_queries += 1

            logger.info(f"Cache hits: {cached_hits}, New queries: {new_queries}")
            
            df.to_parquet(self.output().path, index=False)
        
        except Exception as e:
            logger.error(f"Erro no enriquecimento de feriados: {e}")
            raise e

    def output(self) -> luigi.LocalTarget:
        return luigi.LocalTarget(self.output_path)
