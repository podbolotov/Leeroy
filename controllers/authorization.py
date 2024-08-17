import jwt
import uuid
import datetime
from uuid import UUID
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from jwt import InvalidSignatureError, DecodeError

from controllers.users import UsersController
from database.authorization import AuthorizationDatabaseOperations as AuthDBOps
from database.users import UsersDatabaseOperations as UsersDBOps


class AuthorizationController:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor
        self.secret = "JWT_SIGNATURE_SECRET"
        self.access_token_ttl_minutes = 60  # 1 hour
        self.refresh_token_ttl_minutes = 43200  # 30 days

    def validate_access_token(self, token: str):
        try:

            # Проверяем факт передачи токена
            if token is None:
                reason = "Token is not provided"
                return False, reason, status.HTTP_400_BAD_REQUEST

            # При наличии токена приступаем к его декодированию
            try:
                decoded_token = jwt.decode(token, self.secret, algorithms="HS256")

            # Обрабатываем кейс с некорректной подписью токена
            except InvalidSignatureError:
                reason = "Token has incorrect signature"
                return False, reason, status.HTTP_403_BAD_REQUEST

            # Обрабатываем кейс с общей ошибой декодирования
            except DecodeError:
                reason = "Token malformed or has incorrect format"
                return False, reason, status.HTTP_400_BAD_REQUEST

            # Запрашиваем данные по токену из БД
            token_data_from_db = AuthDBOps.get_token_data_by_id(
                cursor=self.cursor,
                token_type='access',
                token_id=decoded_token['id']
            )

            # Проверяем, что по переданному идентификатору удалось найти запись о токене в БД
            if token_data_from_db is None:
                reason = "Token is not found in database"
                return False, reason, status.HTTP_401_UNAUTHORIZED

            # Проверяем токен на факт отзыва (посредством логаута или рефреша)
            if token_data_from_db[5] is True:
                reason = "Token is revoked"
                return False, reason, status.HTTP_401_UNAUTHORIZED

            # Проверяем токен на истечение
            if self.is_token_expired(token):
                reason = "Provided access_token is expired"
                return False, reason, status.HTTP_403_FORBIDDEN

            return True, 'all checks passed'

        except Exception as e:
            reason = f"Unhandled token processing exception.\n{e}"
            return False, reason, status.HTTP_500_INTERNAL_SERVER_ERROR

    def generate_tokens(self, user_id: UUID):

        # Фиксируем время выпуска пары токенов
        issued_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Фиксируем время истечения access-токена
        access_token_expired_at = (
                datetime.datetime.fromisoformat(issued_at) + datetime.timedelta(minutes=self.access_token_ttl_minutes)
        ).isoformat()

        # Фиксируем время истечения refresh-токена
        refresh_token_expired_at = (
                datetime.datetime.fromisoformat(issued_at) + datetime.timedelta(minutes=self.refresh_token_ttl_minutes)
        ).isoformat()

        access_token_payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "issued_at": issued_at,
            "expired_at": access_token_expired_at
        }

        refresh_token_payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "issued_at": issued_at,
            "expired_at": refresh_token_expired_at
        }

        AuthDBOps.save_token_data(
            connection=self.connection,
            cursor=self.cursor,
            token_type='access',
            token_id=access_token_payload['id'],
            user_id=access_token_payload['user_id'],
            issued_at=access_token_payload['issued_at'],
            expired_at=access_token_payload['expired_at'],
            partner_token_id=refresh_token_payload['id']
        )

        AuthDBOps.save_token_data(
            connection=self.connection,
            cursor=self.cursor,
            token_type='refresh',
            token_id=refresh_token_payload['id'],
            user_id=refresh_token_payload['user_id'],
            issued_at=refresh_token_payload['issued_at'],
            expired_at=refresh_token_payload['expired_at'],
            partner_token_id=access_token_payload['id']
        )

        access_token = jwt.encode(
            access_token_payload,
            self.secret,
            algorithm="HS256"
        )

        refresh_token = jwt.encode(
            refresh_token_payload,
            self.secret,
            algorithm="HS256"
        )

        return access_token, refresh_token

    def is_token_expired(self, token):
        try:
            decoded_token = jwt.decode(token, self.secret, algorithms="HS256")
            expiration_time_as_string = decoded_token['expired_at']
            expiration_timestamp = datetime.datetime.fromisoformat(expiration_time_as_string)
            current_timestamp = datetime.datetime.now(datetime.timezone.utc)
            if expiration_timestamp < current_timestamp:
                return True
            else:
                return False

        except Exception as e:
            raise RuntimeError(f"Unhandled exception on token expiration check\n{e}")

    def authorize_user_by_email_and_password(self, email, password):

        hashed_received_password = UsersController.hash_password(password)

        user_data = UsersDBOps.get_user_data(
            connection=self.connection,
            cursor=self.cursor,
            user_email=email
        )

        if user_data is None:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "UNAUTHORIZED",
                    "description": f"User with email {email} is not found or password is incorrect"
                })

        stored_users_password_hash = user_data[5]

        if hashed_received_password != stored_users_password_hash:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "UNAUTHORIZED",
                    "description": f"User with email {email} is not found or password is incorrect"
                })

        access_token, refresh_token = self.generate_tokens(user_id=user_data[0])
        return JSONResponse(
            status_code=200,
            content={
                "access_token": access_token,
                "refresh_token": refresh_token
            })
