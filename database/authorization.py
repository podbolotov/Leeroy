from uuid import UUID

from database.connect_database import create_db_connection


class AuthorizationDatabaseOperations:
    """
    Данный класс включает в себя CRUD-операции над токенами в БД
    """

    @staticmethod
    def save_token_data(
            token_type: str,
            token_id: str,
            user_id: str,
            issued_at: str,
            expired_at: str,
            partner_token_id: str
    ):

        if token_type == 'access':
            insert_token_query = """
            INSERT INTO public.access_tokens (
                id, user_id, issued_at, expired_at, refresh_token_id, revoked
            ) VALUES (%s,%s,%s,%s,%s,%s)
            """
        elif token_type == 'refresh':
            insert_token_query = """
            INSERT INTO public.refresh_tokens (
                id, user_id, issued_at, expired_at, access_token_id, revoked
            ) VALUES (%s,%s,%s,%s,%s,%s)
            """
        else:
            raise ValueError("Unsupported token type")


        token_data = (token_id, user_id, issued_at, expired_at, partner_token_id, 'false')

        connection = create_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(insert_token_query, token_data)
            connection.commit()
        connection.close()
        return True

    @staticmethod
    def get_token_data_by_id(
            token_type: str,
            token_id: str
    ):
        if token_type == 'access':
            get_token_data_query = 'SELECT * from public.access_tokens WHERE id = %s;'
        elif token_type == 'refresh':
            get_token_data_query = 'SELECT * from public.refresh_tokens WHERE id = %s;'
        else:
            raise ValueError("Unsupported token type")

        connection = create_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(get_token_data_query, (str(token_id),))
            token = cursor.fetchone()
        connection.close()

        return token

    @staticmethod
    def revoke_tokens(
            token_type: str,
            token_id: str
    ):
        connection = create_db_connection()
        try:
            if token_type == 'access':

                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        UPDATE public.access_tokens SET revoked = true::boolean WHERE id = %s;
                        UPDATE public.refresh_tokens SET revoked = true::boolean WHERE access_token_id = %s;
                        ''', (str(token_id), str(token_id))
                    )
                    connection.commit()
                connection.close()

            elif token_type == 'refresh':

                with connection.cursor() as cursor:
                    cursor.execute(
                        '''
                        UPDATE public.refresh_tokens SET revoked = true::boolean WHERE id = %s;
                        UPDATE public.access_tokens SET revoked = true::boolean WHERE refresh_token_id = %s;
                        ''', (str(token_id), str(token_id))
                    )
                    connection.commit()
                connection.close()

            else:
                raise ValueError("Unsupported token type")

            return True

        except Exception as e:
            connection.rollback()
            connection.close()
            raise RuntimeError(f'Tokens revoke request if failed!\n{e}')

