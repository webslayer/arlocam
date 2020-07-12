from pydantic import BaseModel


class Auth(BaseModel):
    email: str
    password: str


class DateRange(BaseModel):
    datefrom: str
    dateto: str
