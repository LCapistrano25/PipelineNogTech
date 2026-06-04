import logging
import os

import luigi

from infrastructure.utils.file_utils import ensure_dir
from pipelines.transform.transform_engagement_transactions import (
    TransformEnrichedDataTask,
)

def setup_logging():
    """
    Configura o logging estruturado para o projeto.
    """
    log_dir = "logs"
    log_file = os.path.join(log_dir, "pipeline.log")
    ensure_dir(log_file)
    
    logging.basicConfig(
        level=logging.INFO,
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
    luigi.build(
        [TransformEnrichedDataTask()],
        local_scheduler=True
    )
    
    logger.info("Pipeline finalizada com sucesso!")
