from pydantic import BaseModel


class DateRange(BaseModel):
    datefrom: str
    dateto: str
