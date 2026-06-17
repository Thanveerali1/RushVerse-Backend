from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str | None = None
    phone: str | None = None
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class BetCreate(BaseModel):
    period: str
    color: str
    amount: int


class RoundResultCreate(BaseModel):
    period: str
    result: str