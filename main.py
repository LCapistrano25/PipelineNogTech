import logging
import os

import luigi
from decouple import config

from config.settings import PIPELINE_LOCAL_SCHEDULER
from infrastructure.utils.file_utils import ensure_dir
from pipelines.load.load_data_lake import LoadDataLakeTask

def setup_logging():
    """
    Configura o logging estruturado para o projeto.
    """
    log_dir = "logs"
    log_file = os.path.join(log_dir, "pipeline.log")
    ensure_dir(log_file)
    
    log_level = config("LOG_LEVEL", default="INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("main")
    
    logger.info("Iniciando a execução da Pipeline ETL NogTech")
    
    # Executa a task final que desencadeia as dependências
    # O local_scheduler=False indica que deve tentar conectar ao central scheduler (Docker)
    luigi.build(
        [LoadDataLakeTask()],
        local_scheduler=PIPELINE_LOCAL_SCHEDULER
    )
    
    logger.info("Pipeline finalizada com sucesso!")
