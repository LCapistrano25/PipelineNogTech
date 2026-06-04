from pydantic import BaseModel

class ResponseHoliday(BaseModel):
    date: str
    name: str
    type: str
    weekday: str