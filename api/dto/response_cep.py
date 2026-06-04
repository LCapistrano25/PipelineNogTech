from pydantic import BaseModel

class ResponseCep(BaseModel):
    cep: str
    state: str
    city: str
    neighborhood: str
    street: str
