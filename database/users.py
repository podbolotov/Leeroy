import uuid


class UsersDatabaseOperations:

    @staticmethod
    def create_new_user(
            connection,
            cursor,
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

        cursor.execute(insert_user_query, user_data)
        connection.commit()
        return user_id

    @staticmethod
    def get_user_data(
            connection,
            cursor,
            user_id: str | None = None,
            user_email: str | None = None,
            find_by: str = 'email'
    ):
        try:
            if find_by == 'email' and user_email is not None:
                cursor.execute('SELECT * from public.users WHERE email = \'%s\';' % str(user_email))
            elif find_by == 'id' and user_id is not None:
                cursor.execute('SELECT * from public.users WHERE id = \'%s\';' % str(user_id))
            else:
                raise ValueError("Unsupported find_by type or missed search query")

            user_data = cursor.fetchone()

            return user_data

        except Exception as e:
            connection.rollback()
            raise RuntimeError(f'Database request if failed!\n{e}')

