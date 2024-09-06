import datetime
import uuid
from uuid import UUID

import jwt
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from jwt import InvalidSignatureError, DecodeError

from controllers.users import UsersController
from data.service_variables import ServiceVariables as SeVars
from database.authorization import AuthorizationDatabaseOperations as AuthDBOps
from database.users import UsersDatabaseOperations as UsersDBOps
from models.authorization import AuthSuccessfulResponse
from models.jwt_tokens import DecodedJsonWebToken, ValidationErrorTokenNotProvided, ValidationErrorTokenBadSignature, \
    ValidationErrorTokenMalformed, ValidationErrorTokenExpired, ValidationErrorTokenNotFoundInDatabase, \
    ValidationErrorTokenRevoked
from models.default_error import DefaultError


class AuthorizationController:
    def __init__(self):
        self.secret = str(SeVars.JWT_SIGNATURE_SECRET)
        self.access_token_ttl_minutes = int(SeVars.ACCESS_TOKEN_TTL_IN_MINUTES)
        self.refresh_token_ttl_minutes = int(SeVars.REFRESH_TOKEN_TTL_IN_MINUTES)

    @staticmethod
    def decode_token_without_validation(token) -> DecodedJsonWebToken:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        return DecodedJsonWebToken(
            id=decoded_token['id'],
            user_id=decoded_token['user_id'],
            issued_at=decoded_token['issued_at'],
            expired_at=decoded_token['expired_at']
        )

    def validate_access_token(self, token: str) -> JSONResponse | bool:
        try:
            # Проверяем факт передачи токена
            if token is None:
                return JSONResponse(
                    status_code=400,
                    content=jsonable_encoder(
                        ValidationErrorTokenNotProvided()
                    ))

            # При наличии токена приступаем к его декодированию
            try:
                decoded_token = jwt.decode(token, self.secret, algorithms="HS256")

            # Обрабатываем кейс с некорректной подписью токена
            except InvalidSignatureError:
                return JSONResponse(
                    status_code=401,
                    content=jsonable_encoder(ValidationErrorTokenBadSignature()))

            # Обрабатываем кейс с общей ошибкой декодирования
            except DecodeError:
                return JSONResponse(
                    status_code=400,
                    content=jsonable_encoder(ValidationErrorTokenMalformed()))

            # Проверяем токен на истечение
            if self.is_token_expired(token):
                return JSONResponse(
                    status_code=401,
                    content=jsonable_encoder(ValidationErrorTokenExpired()))

            # Запрашиваем данные по токену из БД
            token_data_from_db = AuthDBOps.get_token_data_by_id(
                token_type='access',
                token_id=decoded_token['id']
            )

            # Проверяем, что по переданному идентификатору удалось найти запись о токене в БД
            if token_data_from_db is None:
                return JSONResponse(
                    status_code=401,
                    content=jsonable_encoder(ValidationErrorTokenNotFoundInDatabase()))

            # Проверяем токен на факт отзыва (посредством логаута или рефреша)
            if token_data_from_db[5] is True:
                return JSONResponse(
                    status_code=401,
                    content=jsonable_encoder(ValidationErrorTokenRevoked()))

            return True

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content=jsonable_encoder(
                    DefaultError(
                        status="INTERNAL_SERVER_ERROR",
                        description=f"Unhandled token processing exception. {e}"
                    )
                ))

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
            token_type='access',
            token_id=access_token_payload['id'],
            user_id=access_token_payload['user_id'],
            issued_at=access_token_payload['issued_at'],
            expired_at=access_token_payload['expired_at'],
            partner_token_id=refresh_token_payload['id']
        )

        AuthDBOps.save_token_data(
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
            content=AuthSuccessfulResponse(access_token=access_token, refresh_token=refresh_token).model_dump()
        )  # эксперементальный способ возвращения данных при помощи модели

        # return JSONResponse(
        #     status_code=200,
        #     content={
        #         "access_token": access_token,
        #         "refresh_token": refresh_token
        #     })

    def refresh_tokens(self, refresh_token):

        # Начинаем декодирование переданного токена
        try:
            decoded_token = jwt.decode(refresh_token, self.secret, algorithms="HS256")

        # Возвращаем ошибку, если подпись токена некорректна.
        except InvalidSignatureError:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "TOKEN_BAD_SIGNATURE",
                    "description": "Refresh-Token has incorrect signature"
                })

        # Возвращаем ошибку для всех остальных ошибок декодирования.
        except DecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "TOKEN_MALFORMED",
                    "description": "Refresh-Token is malformed or has incorrect format"
                })

        # Возвращаем ошибку в случае, если токен истёк.
        if self.is_token_expired(refresh_token):
            return JSONResponse(
                status_code=401,
                content={
                    "status": "TOKEN_EXPIRED",
                    "description": "Provided Refresh-Token is expired"
                })

        # Если автономные (без запроса данных из БД) проверки прошли успешно - запрашиваем данные по
        # переданному токену из БД, далее проверяем полученные данные.
        refresh_token_data_from_db = AuthDBOps.get_token_data_by_id(
            token_type='refresh',
            token_id=decoded_token['id']
        )

        # Если данные по ID токена найти не удалось, то возвращаем соответствуюшую ошибку.
        if refresh_token_data_from_db is None:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "TOKEN_NOT_FOUND",
                    "description": "Refresh-Token data is not found in database"
                })

        # Если данные по токену были найдены, но токен уже значится отозванным - возвращаем ошибку.
        if refresh_token_data_from_db[5] is True:
            return JSONResponse(
                status_code=401,
                content={
                    "status": "TOKEN_REVOKED",
                    "description": "Refresh-Token is revoked"
                })

        access_token_id = refresh_token_data_from_db[4]  # сохраняем ID access-токена для дальнейшей проверки его отзыва
        refresh_token_id = decoded_token['id']  # сохраняем ID access-токена для его отзыва и дальнейшей проверки
        # его отзыва
        user_id = decoded_token['user_id']  # сохраняем полученный из декодированного токена user_id для его
        # прикрепления к новой паре авторизационных токенов

        # Если  валидация рефреш-токена пройдена успешно, то запускаем
        # процесс отзыва переданной пары токенов и выпуска новой пары.
        try:
            # Запускаем процедуру отзыва токенов
            AuthDBOps.revoke_tokens(
                token_type='refresh',
                token_id=refresh_token_id
            )

            # После завершения работы процедуры отзыва токенов - сохраняем новый статус переданного рефреш-токена.
            is_refresh_token_revoked = AuthDBOps.get_token_data_by_id(
                token_type='refresh',
                token_id=refresh_token_id
            )[5]

            # Также сохраняем новый статус access-токена, который связан с переданным рефреш-токеном и также должен
            # быть отозван.
            is_access_token_revoked = AuthDBOps.get_token_data_by_id(
                token_type='access',
                token_id=access_token_id
            )[5]

            # В случае, если оба токена были успешно отозваны - запускаем генерацию новой пары токенов и возвращаем
            # её пользователю.
            if is_refresh_token_revoked and is_access_token_revoked:

                access_token, refresh_token = self.generate_tokens(user_id=user_id)
                return JSONResponse(
                    status_code=200,
                    content=AuthSuccessfulResponse(access_token=access_token, refresh_token=refresh_token).model_dump()
                )

            # Если один токенов обновляемой пары не был отозван - сообщаем о ошибке.
            else:
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "INTERNAL_SERVER_ERROR",
                        "description": f"Unknown token refreshing exception. Access-Token revoked: "
                                       f"{is_access_token_revoked}, Refresh-Token revoked: {is_refresh_token_revoked}."
                    })

        # Выбрасываем общую ошибку в случае, если при процедуре отзыва токенов или при генерации новой пары возникло
        # необработанное исключение.
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "INTERNAL_SERVER_ERROR",
                    "description": f"Unhandled token refreshing exception. {e}"
                })

    def logout(self, access_token):

        try:
            decoded_token = jwt.decode(access_token, self.secret, algorithms="HS256")
            access_token_id = decoded_token['id']

            refresh_token_id = AuthDBOps.get_token_data_by_id(
                token_type='access',
                token_id=access_token_id
            )[4]

            AuthDBOps.revoke_tokens(
                token_type='access',
                token_id=access_token_id
            )

            is_access_token_revoked = AuthDBOps.get_token_data_by_id(
                token_type='access',
                token_id=access_token_id
            )[5]

            is_refresh_token_revoked = AuthDBOps.get_token_data_by_id(
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
