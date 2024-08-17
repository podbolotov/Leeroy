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

    def validate_access_token(self, token: str) -> JSONResponse | bool:
        try:
            # Проверяем факт передачи токена
            if token is None:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "TOKEN_NOT_PROVIDED",
                        "description": "Access-Token is not provided"
                    })

            # При наличии токена приступаем к его декодированию
            try:
                decoded_token = jwt.decode(token, self.secret, algorithms="HS256")

            # Обрабатываем кейс с некорректной подписью токена
            except InvalidSignatureError:
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "TOKEN_BAD_SIGNATURE",
                        "description": "Access-Token has incorrect signature"
                    })

            # Обрабатываем кейс с общей ошибой декодирования
            except DecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "TOKEN_MALFORMED",
                        "description": "Access-Token is malformed or has incorrect format"
                    })

            # Запрашиваем данные по токену из БД
            token_data_from_db = AuthDBOps.get_token_data_by_id(
                cursor=self.cursor,
                token_type='access',
                token_id=decoded_token['id']
            )

            # Проверяем, что по переданному идентификатору удалось найти запись о токене в БД
            if token_data_from_db is None:
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "TOKEN_NOT_FOUND",
                        "description": "Access-Token data is not found in database"
                    })

            # Проверяем токен на факт отзыва (посредством логаута или рефреша)
            if token_data_from_db[5] is True:
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "TOKEN_REVOKED",
                        "description": "Access-Token is revoked"
                    })

            # Проверяем токен на истечение
            if self.is_token_expired(token):
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "TOKEN_EXPIRED",
                        "description": "Provided Access-Token is expired"
                    })

            return True

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "INTERNAL_SERVER_ERROR",
                    "description": f"Unhandled token processing exception. {e}"
                })

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

    def logout(self, access_token):

        try:
            decoded_token = jwt.decode(access_token, self.secret, algorithms="HS256")
            access_token_id = decoded_token['id']

            refresh_token_id = AuthDBOps.get_token_data_by_id(
                cursor=self.cursor,
                token_type='access',
                token_id=access_token_id
            )[4]

            AuthDBOps.revoke_tokens(
                connection=self.connection,
                cursor=self.cursor,
                token_type='access',
                token_id=access_token_id
            )

            is_access_token_revoked = AuthDBOps.get_token_data_by_id(
                cursor=self.cursor,
                token_type='access',
                token_id=access_token_id
            )[5]

            is_refresh_token_revoked = AuthDBOps.get_token_data_by_id(
                cursor=self.cursor,
                token_type='refresh',
                token_id=refresh_token_id
            )[5]

            if is_access_token_revoked and is_refresh_token_revoked:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "Logout is completed"
                    })
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "INTERNAL_SERVER_ERROR",
                        "description": f"Unknown token revoking exception. Access-Token revoked: "
                                       f"{is_access_token_revoked}, Refresh-Token revoked: {is_refresh_token_revoked}."
                    })

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "INTERNAL_SERVER_ERROR",
                    "description": f"Unhandled token revoking exception. {e}"
                })
