import uuid
from uuid import UUID

from psycopg import errors
from psycopg.rows import namedtuple_row

from database.connect_database import create_db_connection
from database.custom_exceptions import LastAdministratorInDbError

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
                with connection.cursor(row_factory=namedtuple_row) as cursor:
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
    def update_administrator_permissions_by_user_id(
            user_id: str,
            is_admin: bool
    ):
        """ Данный метод обеспечивает обновление признака "is_admin" (наличие прав администратора у пользователя) в БД.

        :param user_id: ID пользователя, признак "is_admin" которого необходимо изменить.
        :param is_admin: Желаемое значение признака "is_admin".
        :raises LastAdministratorInDbError: Ошибка, возвращаемая в случае, если последнему владельцу признака is_admin
        со значением True пытаются присвоить значение False (то есть, при попытке отзыва прав администратора у
        последнего администратора).
        :raises RuntimeError: Общая ошибка для всех необработанных ошибок работы с БД.
        """
        connection = create_db_connection()

        try:
            with connection.cursor(row_factory=namedtuple_row) as cursor:
                if is_admin is True:
                    cursor.execute('UPDATE public.users SET is_admin = true WHERE id = %s;', (str(user_id),) )
                elif is_admin is False:
                    cursor.execute(
                        '''
                        DO
                        $do$
                        BEGIN
                        IF (SELECT COUNT(*) FROM public.users WHERE is_admin = true) <= 1 THEN
                            RAISE EXCEPTION 'LAST_ADMIN';
                        ELSE
                            UPDATE public.users SET is_admin = false WHERE id = %s;
                        END IF;
                        END
                        $do$
                        ''', (str(user_id),)
                    )
                connection.commit()
            connection.close()

        except errors.RaiseException:
            connection.rollback()
            connection.close()
            raise LastAdministratorInDbError("Last administrator permissions can't be revoked!")

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
