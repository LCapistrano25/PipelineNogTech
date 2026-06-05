import os
from decouple import config

# Raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Configurações de Caminhos (Paths)
DATABASES_DIR = os.path.join(BASE_DIR, "databases")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

RAW_ENGAGEMENT_PATH = os.path.join(DATABASES_DIR, "engajamento_alunos.json")
RAW_TRANSACTIONS_PATH = os.path.join(DATABASES_DIR, "transacoes_nogtech.csv")

# Caminhos de Processamento (Parquet)
LOADED_ENGAGEMENT = os.path.join(OUTPUT_DIR, "loaded", "engagement_students.parquet")
LOADED_TRANSACTIONS = os.path.join(OUTPUT_DIR, "loaded", "transactions_nogtech.parquet")

PROCESSED_ENGAGEMENT = os.path.join(OUTPUT_DIR, "processed", "engagement.parquet")
PROCESSED_TRANSACTIONS = os.path.join(OUTPUT_DIR, "processed", "transactions.parquet")
ENRICHED_ADDRESS = os.path.join(OUTPUT_DIR, "processed", "transactions_enriched_address.parquet")
ENRICHED_HOLIDAY = os.path.join(OUTPUT_DIR, "processed", "transactions_enriched_holiday.parquet")
PROCESSED_ANONYMIZED = os.path.join(OUTPUT_DIR, "processed", "transactions_anonymized.parquet")

FINAL_ENRICHED_DATA = os.path.join(OUTPUT_DIR, "transformed", "enriched_engagement_transactions.parquet")
ANONYMIZED_TRANSACTIONS = os.path.join(OUTPUT_DIR, "final", "data_lake")

# Caches
CEP_CACHE_PATH = os.path.join(DATABASES_DIR, "cep_cache.json")
HOLIDAY_CACHE_PATH = os.path.join(DATABASES_DIR, "holiday_cache.json")

# Configurações da API
BRASIL_API_CEP_URL = config("BRASIL_API_CEP_URL", default="https://brasilapi.com.br/api/cep/v2/")
BRASIL_API_HOLIDAY_URL = config("BRASIL_API_HOLIDAY_URL", default="https://brasilapi.com.br/api/feriados/v1/")
API_TIMEOUT = config("API_TIMEOUT", default=15, cast=int)
API_RETRIES = config("API_RETRIES", default=3, cast=int)

# Configurações do Pipeline
PIPELINE_WORKERS = config("PIPELINE_WORKERS", default=1, cast=int)
PIPELINE_LOCAL_SCHEDULER = config("LUIGI_LOCAL_SCHEDULER", default=True, cast=bool)
