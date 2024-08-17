import hashlib
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

