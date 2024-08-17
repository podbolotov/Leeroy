"""
Этот модуль отвечает за базовую логику запуска приложения и машрутизацию на все доступные эндпоинты.
"""

from uuid import UUID

import uvicorn
from fastapi import FastAPI, Request, status, Header, Body, Path
from fastapi.responses import JSONResponse

import models.authorization
from controllers.authorization import AuthorizationController
from controllers.books import BooksController
from controllers.users import UsersController
from database.basic_operations import DatabaseBasicOperations
from models.authorization import (AuthRequestBody, AuthUnauthorizedError, AuthSuccessfulResponse,
                                  LogoutSuccessfulResponse)
from models.books import BookNotFoundError, SingleBook, MultipleBooks

db_basic_ops = DatabaseBasicOperations()
db_connection, db_cursor = db_basic_ops.connect_to_database()


app_description = open('README.md', 'r', encoding="utf-8")
app = FastAPI(
    title="Leeroy",
    description=app_description.read(),
    version="1.0.0"
)

authorization_controller = AuthorizationController(connection=db_connection, cursor=db_cursor)
books_controller = BooksController(connection=db_connection, cursor=db_cursor)
users_controller = UsersController(connection=db_connection, cursor=db_cursor)


@app.middleware("http")
async def authentification_check_middleware(request: Request, call_next):
    access_token = request.headers.get('Access-Token')

    if request.url.path in ['/authorize', '/docs', '/favicon.ico', '/openapi.json', '/redoc']:
        response = await call_next(request)
        return response

    token_validation_results = authorization_controller.validate_access_token(token=access_token)

    if token_validation_results is True:
        response = await call_next(request)
        return response
    else:
        return token_validation_results


@app.post(
    "/authorize",
    status_code=status.HTTP_200_OK,
    response_model=AuthSuccessfulResponse,
    response_description=AuthSuccessfulResponse.__doc__,
    responses={401: {"model": AuthUnauthorizedError, "description": AuthUnauthorizedError.__doc__}},
    tags=["Authorization"]
)
async def authorize(
        request_body: AuthRequestBody = Body()
):
    """
    Данный эндпоинт авторизует пользователя по переданной паре электронной почты и пароля.

    Не находится в авторизованной зоне.

    В ответе возвращает JWT-токены, которые используются для авторизации и аутентификации пользователя на всех
    эндпоинтах, находящихся в авторизованной зоне.
    """
    return authorization_controller.authorize_user_by_email_and_password(
        email=request_body.email,
        password=request_body.password
    )


@app.delete(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=LogoutSuccessfulResponse,
    response_description=LogoutSuccessfulResponse.__doc__,
    # responses={401: {"model": AuthUnauthorizedError, "description": AuthUnauthorizedError.__doc__}},
    tags=["Authorization"]
)
async def logout(
        access_token: str = Header(description="Авторизационный токен")
):
    """
    Данный эндпоинт выполняет инвалидацию пары из авторизационного токена и refresh-токена.

    Требует передачи действительного Access-Token, который не истёк и не был ранее отозван.

    В ответе возвращается статус операции.
    """
    return authorization_controller.logout(access_token)


# Получение всех доступных книг
@app.get(
    path="/books",
    status_code=status.HTTP_200_OK,
    response_model=MultipleBooks,
    tags=["Books"]
)
async def get_all_books(
        access_token: str = Header(description="Авторизационный токен")
):
    """
    Данный эндпоинт возвращает все доступные книги.
    """
    return books_controller.get_all_books()


@app.get(
    "/books/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=SingleBook,
    responses={404: {"model": BookNotFoundError}},
    tags=["Books"]
)
async def get_book_by_id(
        book_id: UUID = Path(description="ID книги, которую требуется найти"),
        access_token: str = Header(description="Авторизационный токен")
):
    """
    Данный эндпоинт возвращает одну книгу, в соответствии с переданным book_id.
    """
    return books_controller.get_book_by_id(book_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
