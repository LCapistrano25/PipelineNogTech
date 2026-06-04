# Configurações globais do projeto ETL NogTech

PATHS = {
    "databases": "databases/",
    "output": "output/",
    "logs": "logs/"
}

# Configurações da API
BRASIL_API = {
    "base_url": "https://brasilapi.com.br/api/cep/v2/",
    "timeout": 10
}

# Configurações do Pipeline
PIPELINE = {
    "local_scheduler": True,
    "workers": 1
}
