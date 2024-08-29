import hashlib
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from data.service_variables import ServiceVariables as SeVars
from database.users import UsersDatabaseOperations as UsersDBOps
from models.default_error import DefaultError
from models.jwt_tokens import DecodedJsonWebToken
from models.users import (CreateUserForbiddenError, CreateUserEmailIsNotAvailableError,
                          CreateUserSuccessfulResponse, GetUserDataSuccessfulResponse, GetUserDataForbiddenError,
                          DeleteUserForbiddenError, GetUserDataNotFoundError, DeleteUserSuccessfulResponse)


class UsersController:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    @staticmethod
    def hash_password(password: str):
        salt = SeVars.PASSWORD_HASH_SALT

        password_prepared_for_hashing = password + salt
        hashed_password = hashlib.md5(password_prepared_for_hashing.encode())

        return hashed_password.hexdigest()

    def create_user(self, requester_decoded_access_token, email, firstname, middlename, surname, password):

        # Извлекаем ID пользователя, запросившего создание нового пользователя.
        requester_id = requester_decoded_access_token.user_id

        # Получаем все данные по запрашивающему из БД
        requester_data = UsersDBOps.get_user_data(
            connection=self.connection,
            cursor=self.cursor,
            find_by='id',
            user_id=requester_id
        )
        # Проверяем наличие признака "администратор" у запрашивающего пользователя.
        if requester_data[6] is False:
            return JSONResponse(
                status_code=403,
                content=jsonable_encoder(
                    CreateUserForbiddenError()
                ))

        is_email_used = UsersDBOps.get_user_data(
            connection=self.connection,
            cursor=self.cursor,
            find_by='email',
            user_email=email
        )

        if is_email_used is not None:
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(
                    CreateUserEmailIsNotAvailableError(
                        description=f"Email {email} is not avalaible for registration")
                ))

        user_id = UsersDBOps.create_new_user(
            connection=self.connection,
            cursor=self.cursor,
            firstname=firstname,
            middlename=middlename,
            surname=surname,
            email=email,
            hashed_password=self.hash_password(password),
            is_admin=False
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                CreateUserSuccessfulResponse(user_id=user_id)
            ))

    def get_user_data(self, decoded_access_token: DecodedJsonWebToken, user_id: UUID = None) -> JSONResponse:

        # ID пользователя, делающего запрос данных по пользователю.
        requester_id = decoded_access_token.user_id

        # Если передан user_id, но он не равен id запрашивающего, значит пользователь ищет информацию не по себе.
        if user_id is not None and requester_id != user_id:

            # Проверяем наличие прав администратора у запрашивающего.
            requester_data = UsersDBOps.get_user_data(
                connection=self.connection,
                cursor=self.cursor,
                find_by='id',
                user_id=str(requester_id)
            )
            is_requester_admin = requester_data[6]

            # Если запрашивающий является администратором - ищем данные по запрошенному пользователю и записываем их.
            if is_requester_admin is True:
                user_data = UsersDBOps.get_user_data(
                    connection=self.connection,
                    cursor=self.cursor,
                    find_by='id',
                    user_id=str(user_id)
                )
            # Если запрашивающий не является администратором - возвращаем ошибку.
            else:
                return JSONResponse(
                    status_code=403,
                    content=jsonable_encoder(GetUserDataForbiddenError()))

        # Если передан user_id, но он равен id запрашивающего, значит пользователь ищет информацию по себе.
        elif user_id is not None and requester_id == user_id:
            user_data = UsersDBOps.get_user_data(
                connection=self.connection,
                cursor=self.cursor,
                find_by='id',
                user_id=str(requester_id)
            )

        # Если user_id не передан, значит пользователь ищет информацию по себе, в качестве поискового критерия
        # используем requester_id из декодированного Access-Token'а.
        elif user_id is None:
            user_data = UsersDBOps.get_user_data(
                connection=self.connection,
                cursor=self.cursor,
                find_by='id',
                user_id=str(requester_id)
            )

        # Запрос не удалось сопоставить ни с одним из ожидаемых сценариев.
        else:
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(
                    DefaultError(
                        status="INTERNAL_SERVER_ERROR",
                        description="Unexpected case in user data find operation"
                    )
                ))

        # Если в результате поиска в переменную user_data не были записаны данные по искомому
        # пользователю - возвращаем соответствующую ошибку.
        if user_data is None:
            return JSONResponse(
                status_code=404,
                content=jsonable_encoder(
                    GetUserDataNotFoundError(description=f"User with id {user_id} is not found.")
                ))

        # В случае, если все проверки пройдены успешно - возвращаем запрошенную информацию.
        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                GetUserDataSuccessfulResponse(
                    id=user_data[0],
                    firstname=user_data[1],
                    middlename=user_data[2],
                    surname=user_data[3],
                    email=user_data[4],
                    is_admin=user_data[6]
                ), exclude_none=True
            ))

    def delete_user(self, decoded_access_token: DecodedJsonWebToken, user_id: UUID) -> JSONResponse:
        # ID пользователя, делающего запрос на удаление пользователя.
        requester_id = decoded_access_token.user_id

        # Проверяем наличие прав администратора у запрашивающего.
        requester_data = UsersDBOps.get_user_data(
            connection=self.connection,
            cursor=self.cursor,
            find_by='id',
            user_id=str(requester_id)
        )
        is_requester_admin = requester_data[6]

        # Если запрашивающий является администратором - ищем данные по запрошенному пользователю и записываем их.
        if is_requester_admin is True:

            # Проверяем, существует ли пользователь, которого пытаются удалить.
            user_for_delete_data = UsersDBOps.get_user_data(
                connection=self.connection,
                cursor=self.cursor,
                find_by='id',
                user_id=str(user_id)
            )

            # Если пользователя не существует, то возвращаем соответствующую ошибку.
            if user_for_delete_data is None:
                return JSONResponse(
                    status_code=404,
                    content=jsonable_encoder(
                        GetUserDataNotFoundError(description=f"User with id {user_id} is not found.")
                    ))

            # Если пользователь является администратором - возвращаем соответствующую ошибку.
            is_user_for_delete_admin = user_for_delete_data[6]
            if is_user_for_delete_admin is True:
                return JSONResponse(
                    status_code=403,
                    content=jsonable_encoder(
                        DeleteUserForbiddenError(description="Administrator can not be deleted"))
                )

            # Удаляем пользователя и все выпущенные на него токены в БД
            UsersDBOps.delete_user_and_delete_all_users_tokens_by_user_id(
                connection=self.connection,
                cursor=self.cursor,
                user_id=user_id
            )

            # В случае успешного удаления - возвращаем статусное сообщение.
            return JSONResponse(
                status_code=200,
                content=jsonable_encoder(DeleteUserSuccessfulResponse())
            )

        # Если запрашивающий не является администратором - возвращаем ошибку.
        else:
            return JSONResponse(
                status_code=403,
                content=jsonable_encoder(DeleteUserForbiddenError(description="Only administrators can delete users"))
            )
