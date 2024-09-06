import uuid
from uuid import UUID
from database.connect_database import create_db_connection

class UsersDatabaseOperations:

    @staticmethod
    def create_new_user(
            firstname: str,
            surname: str,
            email: str,
            hashed_password: str,
            is_admin: bool,
            middlename: str | None = None,
    ):

        insert_user_query = """
        INSERT INTO public.users (
            id, firstname, middlename, surname, email, hashed_password, is_admin
        ) VALUES (%s,%s,%s,%s,%s,%s,%s)
        """

        user_id = str(uuid.uuid4())

        user_data = (
            user_id,
            firstname,
            middlename,
            surname,
            email,
            hashed_password,
            is_admin
        )

        connection = create_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(insert_user_query, user_data)
            connection.commit()
        connection.close()
        return user_id

    @staticmethod
    def get_user_data(
            user_id: str | None = None,
            user_email: str | None = None,
            find_by: str = 'email'
    ):
            connection = create_db_connection()

            try:
                with connection.cursor() as cursor:
                    if find_by == 'email' and user_email is not None:
                        cursor.execute('SELECT * from public.users WHERE email = %s;', (str(user_email),))
                    elif find_by == 'id' and user_id is not None:
                        cursor.execute('SELECT * from public.users WHERE id = %s;', (str(user_id),))
                    else:
                        raise ValueError("Unsupported find_by type or missed search query")
                    user_data = cursor.fetchone()

                connection.close()
                return user_data

            except Exception as e:
                connection.rollback()
                connection.close()
                raise RuntimeError(f'Database request if failed!\n{e}')

    @staticmethod
    def delete_user_and_delete_all_users_tokens_by_user_id(
            user_id: UUID
    ):
        connection = create_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE from public.users WHERE id = %s;', (str(user_id),))
                connection.commit()
            connection.close()
        except Exception as e:
            connection.rollback()
            connection.close()
            raise RuntimeError(f'Database request if failed!\n{e}')
