import requests
from api.dto.response_cep import ResponseCep

class APIBrasilRequestCep:
    def __init__(self, cep):
        self.cep = cep
        
    def get_cep(self):
        url = f"https://brasilapi.com.br/api/cep/v2/{self.cep}"
        response = requests.get(url)
        return ResponseCep(**response.json())