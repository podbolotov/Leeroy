from typing import Optional
from typing_extensions import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from models.default_error import DefaultError


class UserDataModel(BaseModel):
    """
    Модель для получения данных по пользователю из БД.

    Временно не используется.
    """
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
    firstname: str = Field(min_length=1, max_length=99)  # , pattern=r"[A-Z]\d{9}"
    """ Имя создаваемого пользователя """
    middlename: Optional[Annotated[str, Field(min_length=1, max_length=99)]] = None
    """ Отчество создаваемого пользователя (опционально) """
    surname: str = Field(min_length=1, max_length=99)
    """ Фамилия создаваемого пользователя """
    password: str = Field(min_length=8, max_length=99)
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
