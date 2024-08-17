import hashlib
from database.users import UsersDatabaseOperations as UsersDBOps

PASSWORD_HASH_SALT = "temporary_passwords_hash_salt"


class UsersController:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    @staticmethod
    def hash_password(password: str):
        salt = PASSWORD_HASH_SALT

        password_prepared_for_hashing = password + salt
        hashed_password = hashlib.md5(password_prepared_for_hashing.encode())

        return hashed_password.hexdigest()

