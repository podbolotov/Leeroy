from uuid import UUID
from typing import List
from pydantic import BaseModel, RootModel
from models.default_error import DefaultError


class BookNotFoundError(DefaultError):
    status: str
    description: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "NOT_FOUND",
                    "description": "Book with ID 47d9ba5e-7a97-473f-850a-65c422e32279 is not found"
                }
            ]
        }
    }


class SingleBook(BaseModel):
    id: UUID
    title: str
    author: str
    isbn: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "47d9ba5e-7a97-473f-850a-65c422e32279",
                    "title": "Простой Python. Современный стиль программирования. 2-е изд.",
                    "author": "Любанович Б.",
                    "isbn": "978-5-4461-1639-3"
                }
            ]
        }
    }


class MultipleBooks(RootModel):
    root: List[SingleBook]

    model_config = {
        "json_schema_extra": {
            "examples": [
                [
                    {
                        "id": "47d9ba5e-7a97-473f-850a-65c422e32279",
                        "title": "Простой Python. Современный стиль программирования. 2-е изд.",
                        "author": "Любанович Б.",
                        "isbn": "978-5-4461-1639-3"
                    }
                ]
            ]
        }
    }

