"""
Этот модуль отвечает за базовую логику запуска приложения и машрутизацию на все доступные эндпоинты.
"""
from uuid import UUID

import uvicorn
from fastapi import FastAPI, Request, status, Header, Body, Path
from fastapi.encoders import jsonable_encoder

from controllers.authorization import AuthorizationController
from controllers.books import BooksController
from controllers.users import UsersController
from database.initialization_script import DatabaseBasicOperations
from models.authorization import AuthRequestBody, RefreshRequestBody, AuthUnauthorizedError, AuthSuccessfulResponse, \
    LogoutSuccessfulResponse
from models.book_units import BookUnitHasActualReservationsError
from models.books import BookNotFoundError, SingleBook, MultipleBooks, CreateBookRequestBody, \
    CreateBookSuccessfulResponse, CreateBookForbiddenError, CreateBookNotUniqueIsbnError, DeleteBookForbiddenError, \
    DeleteBookSuccessfulResponse
from models.users import CreateUserRequestBody, CreateUserForbiddenError, GetUserDataForbiddenError, \
    CreateUserEmailIsNotAvailableError, CreateUserSuccessfulResponse, DeleteUserSuccessfulResponse, \
    GetUserDataSuccessfulResponse, GetUserDataNotFoundError, DeleteUserForbiddenError, PermissionActions, \
    ChangeUserPermissionsValueError, ChangeUserPermissionSuccessfulResponse, ChangeUserPermissionsForbiddenError
from data.available_without_auth import pathes as available_without_auth_pathes

db_basic_ops = DatabaseBasicOperations()
db_basic_ops.init_database()

app_description = open('docs/swagger_descriptions.md', 'r', encoding="utf-8")
app = FastAPI(
    title="Leeroy",
    description=app_description.read(),
    version="0.5.0"
)

authorization_controller = AuthorizationController()
books_controller = BooksController()
users_controller = UsersController()


@app.middleware("http")
async def authentification_check_middleware(request: Request, call_next):
    access_token = request.headers.get('Access-Token')

    if request.url.path in available_without_auth_pathes:
        response = await call_next(request)
        return response

    token_validation_results = authorization_controller.validate_access_token(token=access_token)

    if token_validation_results is True:
        response = await call_next(request)
        return response
    else:
        return token_validation_results


@app.post(
    "/v1/authorize",
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


@app.post(
    "/v1/refresh",
    status_code=status.HTTP_200_OK,
    response_model=AuthSuccessfulResponse,
    response_description=AuthSuccessfulResponse.__doc__,
    # responses={401: {"model": AuthUnauthorizedError, "description": AuthUnauthorizedError.__doc__}},
    tags=["Authorization"]
)
async def refresh(
        request_body: RefreshRequestBody = Body()
):
    """
    Данный эндпоинт выпускает новую пару авторизационного токена и рефреш-токена при передаче корректного рефреш-токена.

    Не находится в авторизованной зоне.

    В ответе возвращает JWT-токены, которые используются для авторизации и аутентификации пользователя на всех
    эндпоинтах, находящихся в авторизованной зоне.
    """
    return authorization_controller.refresh_tokens(
        refresh_token=request_body.refresh_token
    )


@app.delete(
    "/v1/logout",
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


@app.post(
    "/v1/users",
    status_code=status.HTTP_200_OK,
    response_model=CreateUserSuccessfulResponse,
    response_description=CreateUserSuccessfulResponse.__doc__,
    responses={
        400: {
            "model": CreateUserEmailIsNotAvailableError,
            "description": CreateUserEmailIsNotAvailableError.__doc__
        },
        403: {
            "model": CreateUserForbiddenError,
            "description": CreateUserForbiddenError.__doc__
        },
    },
    tags=["Users"]
)
async def create_user(
        access_token: str = Header(description="Авторизационный токен администратора"),
        request_body: CreateUserRequestBody = Body()
):
    """
    Данный эндпоинт регистрирует нового пользователя по переданным данным.

    Среди переданных данных должны быть:
    - Валидный адрес электронной почты, не использующийся ни одним из существующих пользователей.
    - Имя
    - Отчество / среднее имя (опционально)
    - Фамилия
    - Пароль

    Запрос находится в авторизованной зоне и требует передачи Access-Token'а пользователя, наделённого правами
    администратора.

    При успешной регистрации в ответе возвращается статусное сообщение и ID зарегистрированного пользователя.
    """
    return users_controller.create_user(
        requester_decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        email=request_body.email,
        firstname=request_body.firstname,
        middlename=request_body.middlename,
        surname=request_body.surname,
        password=request_body.password
    )


@app.get(
    path="/v1/users/me",
    status_code=status.HTTP_200_OK,
    response_model=GetUserDataSuccessfulResponse,
    response_description=GetUserDataSuccessfulResponse.__doc__,
    tags=["Users"]
)
async def get_user_data_by_access_token(
        access_token: str = Header(description="Авторизационный токен")
):
    """
    Данный эндпоинт возвращает информацию по пользователю, идентифицируя его по переданному Access-Token'у.
    """
    return users_controller.get_user_data(
        decoded_access_token=authorization_controller.decode_token_without_validation(access_token)
    )


@app.get(
    path="/v1/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=GetUserDataSuccessfulResponse,
    response_description=GetUserDataSuccessfulResponse.__doc__,
    responses={
        403: {
            "model": GetUserDataForbiddenError,
            "description": GetUserDataForbiddenError.__doc__
        },
        404: {
            "model": GetUserDataNotFoundError,
            "description": GetUserDataNotFoundError.__doc__
        },
    },
    tags=["Users"]
)
async def get_user_data_by_user_id(
        access_token: str = Header(description="Авторизационный токен"),
        user_id: UUID = Path(description="ID пользователя, данные по которому требуется найти"),
):
    """
    Данный эндпоинт возвращает информацию по пользователю.

    Если пользователь передаст в качестве user_id собственный идентификатор - то он получит информацию о себе аналогично
    запросу GET /users/me.

    Если пользователь передаст идентификатор другого пользователя - то данные другого пользователя будут возвращены
    ему только в случае, если он является администратором.
    """
    return users_controller.get_user_data(
        decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        user_id=user_id
    )


@app.patch(
    "/v1/users/admin-permissions/{user_id}/{permission_action}",
    status_code=status.HTTP_200_OK,
    response_model=ChangeUserPermissionSuccessfulResponse,
    response_description=ChangeUserPermissionSuccessfulResponse.__doc__,
    responses={
        400: {
            "model": ChangeUserPermissionsValueError,
            "description": ChangeUserPermissionsValueError.__doc__
        },
        403: {
            "model": ChangeUserPermissionsForbiddenError,
            "description": ChangeUserPermissionsForbiddenError.__doc__
        },
        404: {
            "model": GetUserDataNotFoundError,
            "description": GetUserDataNotFoundError.__doc__
        }
    },
    tags=["Users"]
)
async def change_user_permissions(
        access_token: str = Header(description="Авторизационный токен администратора"),
        user_id: UUID = Path(description="ID пользователя, права которого необходимо изменить"),
        permission_action: PermissionActions = Path(description="Действие над правами пользователя")
):
    """
    Данный эндпоинт меняет права администратора для пользователя, ID которого передан в запросе.

    Запрос находится в авторизованной зоне и требует передачи Access-Token'а пользователя, наделённого правами
    администратора.

    Обратите внимание, что если пользователь, ID которого передан, является последним пользователем с правами
    администратора, то понизить уровень прав такого пользователя не удастся.

    При успешной смене прав в ответе возвращается статусное сообщение и новое значение признака наличия
    администраторских прав у пользователя, уровень прав которого был изменён.

    """
    return users_controller.change_user_permission(
        decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        user_id=user_id,
        permission_action=permission_action
    )


@app.delete(
    "/v1/users/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteUserSuccessfulResponse,
    response_description=DeleteUserSuccessfulResponse.__doc__,
    responses={
        403: {
            "model": DeleteUserForbiddenError,
            "description": DeleteUserForbiddenError.__doc__
        },
        404: {
            "model": GetUserDataNotFoundError,
            "description": GetUserDataNotFoundError.__doc__
        }
    },
    tags=["Users"]
)
async def delete_user(
        access_token: str = Header(description="Авторизационный токен администратора"),
        user_id: UUID = Path(description="ID пользователя, которого необходимо удалить"),
):
    """
    Данный эндпоинт удаляет пользователя по переданному ID.

    Удаление является окончательным, при успешном исходе - удаляется запись о пользователе, все его авторизационные
    токены (активные, истёкшие, отозыванные) и все прочие сущности, связанные с удаляемым пользователем.

    Запрос находится в авторизованной зоне и требует передачи Access-Token'а пользователя, наделённого правами
    администратора.

    При успешном удалении в ответе возвращается статусное сообщение.
    """
    return users_controller.delete_user(
        decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        user_id=user_id
    )


@app.post(
    path="/v1/books",
    status_code=status.HTTP_200_OK,
    response_model=CreateBookSuccessfulResponse,
    responses={
        400: {
            "model": CreateBookNotUniqueIsbnError,
            "description": CreateBookNotUniqueIsbnError.__doc__
        },
        403: {
            "model": CreateBookForbiddenError,
            "description": CreateBookForbiddenError.__doc__
        }
    },
    tags=["Books"]
)
async def create_book(
        access_token: str = Header(description="Авторизационный токен администратора"),
        request_body: CreateBookRequestBody = Body()
):
    """
    Данный эндпоинт добавляет в каталог новую книгу по переданным данным.

    Среди переданных данных должны быть:
    - Заголовок книги
    - Автор
    - ISBN (10 или 13 знаков)

    Запрос находится в авторизованной зоне и требует передачи Access-Token'а пользователя, наделённого правами
    администратора.

    ISBN проверяется на уникальность: если книга с переданным ISBN уже существует в базе данных, то будет возвращена
    соответствующая ошибка.

    Формат переданного ISBN не изменяется: если был передан десятизначный номер, то он будет сохранён "как есть".

    Валидация ISBN сведена к проверке длины и состава символов (допускаются только цифры и завершающий X для
    десятизначного ISBN, вычисление контрольных сумм не производится).

    При успешном добавлении книги в ответе возвращается статусное сообщение и ID созданной книги.
    """
    return books_controller.create_book(
        requester_decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        request_body=request_body
    )


@app.get(
    path="/v1/books",
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
    "/v1/books/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=SingleBook,
    responses={
        404: {
            "model": BookNotFoundError,
            "description": BookNotFoundError.__doc__
        }
    },
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


@app.delete(
    "/v1/books/{book_id}",
    status_code=status.HTTP_200_OK,
    response_model=DeleteBookSuccessfulResponse,
    response_description=DeleteBookSuccessfulResponse.__doc__,
    responses={
        403:
            {
                "description": "Ошибка с данным кодом может быть возвращена в случае отсутствия прав администратора "
                               "либо наличия забронированных (выданных) экземпляров книги, запрос на удаление которой "
                               "был получен.",
                "content": {
                    "application/json": {
                        "schema": {
                            "oneOf": [
                                    DeleteBookForbiddenError.model_json_schema(),
                                    BookUnitHasActualReservationsError.model_json_schema()
                            ]
                        },
                        "examples": {
                            "Отправитель запроса не является администратором": {
                                "value": jsonable_encoder(DeleteBookForbiddenError())
                            },
                            "За книгой закреплены забронированные (выданные) экземпляры": {
                                "value": jsonable_encoder(
                                    BookUnitHasActualReservationsError(
                                        description="Book with ID 47d9ba5e-7a97-473f-850a-65c422e32279 has actual "
                                                    "reservations and cannot be deleted"
                                    ))
                            },
                        }
                    }
                },
            },
        404: {
            "model": BookNotFoundError,
            "description": BookNotFoundError.__doc__
        }
    },
    tags=["Books"]
)
async def delete_book_by_id(
        book_id: UUID = Path(description="ID книги, которую требуется удалить"),
        access_token: str = Header(description="Авторизационный токен администратора")
):
    """
    Данный эндпоинт удаляет книгу из системы.

    При удалении книги проверяется отсутствие невозвращённых экземпляров: если будет обнаружено, что какие-то
    экземпляры книги находятся в бронировании, то в удалении книги будет отказано.

    При отсутствии забронированных экземпляров все свободные (доступные для бронирования) экземпляры будут удалены из
    системы вместе с удаляемой книгой.

    Запрос находится в авторизованной зоне и требует передачи Access-Token'а пользователя, наделённого правами
    администратора.

    При успешном удалении книги в ответе возвращается статусное сообщение и ID созданной книги.
    """
    return books_controller.delete_book(
        requester_decoded_access_token=authorization_controller.decode_token_without_validation(access_token),
        book_id=book_id
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
