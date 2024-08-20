from uuid import UUID
from pydantic import BaseModel
from models.default_error import DefaultError


class DecodedJsonWebToken(BaseModel):
    id: UUID
    user_id: UUID
    issued_at: str
    expired_at: str


class ValidationErrorTokenNotProvided(DefaultError):
    status: str = "TOKEN_NOT_PROVIDED"
    description: str = "Access-Token is not provided"


class ValidationErrorTokenBadSignature(DefaultError):
    status: str = "TOKEN_BAD_SIGNATURE"
    description: str = "Access-Token has incorrect signature"


class ValidationErrorTokenMalformed(DefaultError):
    status: str = "TOKEN_MALFORMED"
    description: str = "Access-Token is malformed or has incorrect format"


class ValidationErrorTokenExpired(DefaultError):
    status: str = "TOKEN_EXPIRED"
    description: str = "Provided Access-Token is expired"


class ValidationErrorTokenNotFoundInDatabase(DefaultError):
    status: str = "TOKEN_NOT_FOUND"
    description: str = "Access-Token data is not found in database"


class ValidationErrorTokenRevoked(DefaultError):
    status: str = "TOKEN_REVOKED"
    description: str = "Access-Token is revoked"

