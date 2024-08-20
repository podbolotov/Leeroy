import hashlib
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from models.users import CreateUserRequestBody, CreateUserForbiddenError, CreateUserEmailIsNotAvailableError, \
    CreateUserSuccessfulResponse
from database.users import UsersDatabaseOperations as UsersDBOps
from data.service_variables import ServiceVariables as SeVars


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
                content=jsonable_encoder(CreateUserForbiddenError())
            )

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
