from pydantic import BaseModel, EmailStr
from models.default_error import DefaultError


class AuthRequestBody(BaseModel):
    """ Тело запроса авторизации по электронной почте и паролю. """
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "example@example.com",
                    "password": "ExamplePassw0rd!"
                }
            ]
        }
    }


class AuthUnauthorizedError(DefaultError):
    """ Универсальный ответ, возвращаемый в случае невозможности найти пользователя или в случае, если передан
    некорректный пароль. """
    status: str = "UNAUTHORIZED"
    description: str = "User with email example@contoso.com is not found or password is incorrect"


class AuthSuccessfulResponse(BaseModel):
    """ В случае успешной авторизации возвращается пара из токена доступа и рефреш-токена. """
    access_token: str
    refresh_token: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjVjZTc2NGMxLWRjNTctNGFlMS05Mzk4LWEyZ"
                                    "WUzNmQ3OGQ0ZCIsInVzZXJfaWQiOiI0Y2E3YWE1MC02MDBmLTQ4MjgtOWZiNy00NDVmMDJjMWE0MmQiLCJ"
                                    "pc3N1ZWRfYXQiOiIyMDI0LTA4LTE1VDE2OjA3OjQ1LjE4NDgzOCswMDowMCIsImV4cGlyZWRfYXQiOiIyM"
                                    "DI0LTA4LTE1VDE3OjA3OjQ1LjE4NDgzOCswMDowMCJ9.PYGCYhiRULmwq3OyXQ6Rt2iedrsEXnYTVzbGUS"
                                    "tdcd8",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImZmMjk1OTA4LTYwNzQtNDAzYy1hOTlhLWQx"
                                     "ZDM2NDAwZjgzNSIsInVzZXJfaWQiOiI0Y2E3YWE1MC02MDBmLTQ4MjgtOWZiNy00NDVmMDJjMWE0MmQiL"
                                     "CJpc3N1ZWRfYXQiOiIyMDI0LTA4LTE1VDE2OjA3OjQ1LjE4NDgzOCswMDowMCIsImV4cGlyZWRfYXQiOi"
                                     "IyMDI0LTA5LTE0VDE2OjA3OjQ1LjE4NDgzOCswMDowMCJ9.DMcQZWd7beS1uoquSCyu_S975kL86LqXPA"
                                     "mSKO58iUs"
                }
            ]
        }
    }


class LogoutSuccessfulResponse(BaseModel):
    """ Статусный ответ, возвращаемый при успешной инвалидации пары токенов. """
    status: str = "Logout is completed"
