from pydantic import BaseModel


class DefaultError(BaseModel):
    status: str
    description: str

