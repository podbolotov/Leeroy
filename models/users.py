from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr
from models.default_error import DefaultError


class UserDataModel(BaseModel):
    id: UUID
    """ UUIDv4-идентификатор пользователя"""
    firstname: str
    """ Имя пользователя"""
    middlename: str | None
    """ Отчество пользователя (при наличии)"""
    surname: str
    """ Фамилия пользователя """
    email: EmailStr
    """ Адрес электронной почты пользователя """
    hashed_password: str
    """ Хэш пароля пользователя """
    is_admin: bool
    """ Признак прав администратора у пользователя """


class CreateUserRequestBody(BaseModel):
    email: EmailStr
    """ Желаемый адрес электронной почты создаваемого пользователя """
    firstname: str
    """ Имя создаваемого пользователя"""
    middlename: Optional[str | None] = None
    """ Отчество создаваемого пользователя (опционально)"""
    surname: str
    """ Фамилия создаваемого пользователя """
    password: str
    """ Желаемый пароль создаваемого пользователя """

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "example@contoso.com",
                    "firstname": "Leeroy",
                    "middlename": "Pals for Life",
                    "surname": "Jenkins",
                    "password": "NewUse4Pa55word!"
                }
            ]
        }
    }


class CreateUserForbiddenError(DefaultError):
    """ Данная ошибка возвращается в случае, если зарегистировать нового пользователя пытаются с передачей токена,
    выпущенного на имя сущестующего пользователя, не наделённого правами администратора."""
    status: str = "FORBIDDEN"
    description: str = "Only administrators can create new users"


class CreateUserEmailIsNotAvailableError(DefaultError):
    """ Данная ошибка возвращается в случае, если переданный при попытке регистрации адрес электронной почты
    недоступен для регистрации (например, если он уже используется одним из зарегистрированных пользователей)."""
    status: str = "EMAIL_IS_NOT_AVAILABLE"
    description: str = "Email example@contoso.com is not avalaible for registration"


class CreateUserSuccessfulResponse(BaseModel):
    """ В случае успешной регистрации пользователя возвращается статусное сообщение и ID созданного пользователя. """
    status: str = "User successfully created"
    user_id: UUID

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "User successfully created",
                    "user_id": "8795a12c-5ed7-452a-b9e9-02da8aaa9f37"
                }
            ]
        }
    }
