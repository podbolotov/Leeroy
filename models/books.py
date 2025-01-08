from uuid import UUID
from typing import List, Literal
from pydantic import BaseModel, RootModel, Field, field_validator
from pydantic_core import PydanticCustomError
from pydantic_extra_types.isbn import ISBN
from models.default_error import DefaultError

class CreateBookRequestBody(BaseModel):
    title: str = Field(min_length=1, max_length=99)
    """ Название добавляемой книги """
    author: str = Field(min_length=1, max_length=99)
    """ Имя автора добавляемой книги """
    isbn: str = Field(min_length=10, max_length=13)
    """ Международный стандартный книжный номер (10 или 13 знаков) """

    @field_validator('isbn')
    def isbn_value_must_be_valid_isbn(cls, value):
        try:
            ISBN.validate_isbn_format(value)
        except UnboundLocalError:
            raise PydanticCustomError(
                'isbn_invalid_digit_check_isbn10',
                'Provided digit is invalid for given ISBN'
            )
        except Exception as e:
            raise ValueError(e)
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "author": "Любанович Б.",
                    "title": "Простой Python. Современный стиль программирования. 2-е изд.",
                    "isbn": "9785446116393"
                }
            ]
        }
    }

class CreateBookNotUniqueIsbnError(DefaultError):
    """ Данная ошибка возвращается в случае, если книга с переданным ISBN уже существует в базе данных. """
    status: Literal["NOT_UNIQUE_ISBN"] = "NOT_UNIQUE_ISBN"
    description: str = "Book with ISBN 9783161484100 already exist"

class CreateBookForbiddenError(DefaultError):
    """ Данная ошибка возвращается в случае, если запрос на добавление книги осуществляется от имени пользователя,
    не наделённого правами администратора."""
    status: str = "FORBIDDEN"
    description: str = "Only administrators can add new books"

class DeleteBookForbiddenError(DefaultError):
    """ Данная ошибка возвращается в случае, если запрос на удаление книги осуществляется от имени пользователя,
    не наделённого правами администратора."""
    status: str = "FORBIDDEN"
    description: str = "Only administrators can delete books"

class CreateBookSuccessfulResponse(BaseModel):
    """ В случае успешного добавления новой книги возвращается статусное сообщение и ID добавленной книги. """
    status: Literal["Book successfully added"] = "Book successfully added"
    book_id: UUID

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "Book successfully added",
                    "book_id": "8795a12c-5ed7-452a-b9e9-02da8aaa9f37"
                }
            ]
        }
    }

class DeleteBookSuccessfulResponse(BaseModel):
    """ В случае успешного удаления книги возвращается статусное сообщение. """
    status: str = "Book successfully deleted"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "Book successfully deleted"
                }
            ]
        }
    }

class BookNotFoundError(DefaultError):
    """ Данная ошибка возвращается в случае, если по переданному ID книгу найти не удалось. """
    status: str = "NOT_FOUND"
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
                    "isbn": "9785446116393"
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
                        "isbn": "9785446116393"
                    }
                ]
            ]
        }
    }

