from pydantic import BaseModel, Field

class ResponseCep(BaseModel):
    """
    Entidade que representa a resposta de consulta de CEP da BrasilAPI.
    """
    cep: str = Field(..., description="O CEP consultado")
    state: str = Field(..., description="A sigla do estado")
    city: str = Field(..., description="O nome da cidade")
    neighborhood: str = Field(..., description="O nome do bairro")
    street: str = Field(..., description="O nome do logradouro")
