from pydantic import BaseModel

class HolidayResponse(BaseModel):
    date: str
    name: str
    type: str
    weekday: str