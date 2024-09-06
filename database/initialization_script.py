from data.users import DefaultAdministrator
from database.connect_database import create_db_connection
from database.books import BooksDatabaseOperations as BooksDBOps
from database.users import UsersDatabaseOperations as UsersDBOps
from controllers.users import UsersController
from data.service_variables import ServiceVariables as SeVars


class DatabaseBasicOperations:
    """
    Данный класс включает в себя базовые операции с БД,
    такие как: установка подключения, создание БД при необходимости,
    сброс БД.
    """

    def __init__(self):
        self.user = str(SeVars.DB_USER)
        self.password = str(SeVars.DB_PASSWORD)
        self.host = str(SeVars.DB_HOST)
        self.port = str(SeVars.DB_PORT)

    def init_database(self):

        connection = create_db_connection(target='postgres')
        # Создаём курсор
        cursor = connection.cursor()
        # Проверяем существование базы данных "leeroy".
        cursor.execute('SELECT datname FROM pg_database WHERE datname = \'leeroy\'')
        leeroy_in_exist = cursor.fetchone()

        if leeroy_in_exist is None:
            connection.close()
            self.create_leeroy_database()
        else:
            print("Leeroy DB is exist.")
            connection.close()

    def create_leeroy_database(self):
        connection = create_db_connection(target='postgres')
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE DATABASE leeroy
                    WITH
                    OWNER = %s
                    ENCODING = 'UTF8'
                    LOCALE_PROVIDER = 'libc'
                    CONNECTION LIMIT = -1
                    IS_TEMPLATE = False;
                ''' % str(self.user)
            )
            cursor.execute(
            '''
            ALTER DATABASE leeroy SET timezone TO 'UTC';
            '''
        )
        connection.close()

        connection = create_db_connection()
        connection.autocommit = True

        print("DB created. Creating tables...")
        with connection.cursor() as cursor:
            cursor.execute(
                '''
                CREATE TABLE public.users
                (
                    id uuid NOT NULL,
                    firstname text NOT NULL,
                    middlename text,
                    surname text NOT NULL,
                    email text NOT NULL,
                    hashed_password text NOT NULL,
                    is_admin boolean NOT NULL DEFAULT false,
                    PRIMARY KEY (id),
                    UNIQUE (email)
                );
    
                ALTER TABLE IF EXISTS public.users
                    OWNER to %s;
                ''' % str(self.user)
            )

            hashed_default_user_password = UsersController.hash_password(DefaultAdministrator.password)
            UsersDBOps.create_new_user(
                firstname=DefaultAdministrator.firstname,
                middlename=DefaultAdministrator.middlename,
                surname=DefaultAdministrator.surname,
                email=DefaultAdministrator.email,
                hashed_password=hashed_default_user_password,
                is_admin=DefaultAdministrator.is_admin
            )

            cursor.execute(
                '''
                CREATE TABLE public.access_tokens
                (
                    id uuid NOT NULL,
                    user_id uuid NOT NULL,
                    issued_at timestamp with time zone NOT NULL,
                    expired_at timestamp with time zone NOT NULL,
                    refresh_token_id uuid NOT NULL,
                    revoked boolean NOT NULL DEFAULT false,
                    PRIMARY KEY (id),
                    CONSTRAINT fk_user
                        FOREIGN KEY(user_id) 
                            REFERENCES public.users(id)
                            ON DELETE CASCADE
                );
                
                ALTER TABLE IF EXISTS public.access_tokens
                    OWNER to %s;
                ''' % str(self.user)
            )
            cursor.execute(
                '''
                CREATE TABLE public.refresh_tokens
                (
                    id uuid NOT NULL,
                    user_id uuid NOT NULL,
                    issued_at timestamp with time zone NOT NULL,
                    expired_at timestamp with time zone NOT NULL,
                    access_token_id uuid NOT NULL,
                    revoked boolean NOT NULL DEFAULT false,
                    PRIMARY KEY (id),
                    CONSTRAINT fk_user
                        FOREIGN KEY(user_id) 
                            REFERENCES public.users(id)
                            ON DELETE CASCADE
                );
    
                ALTER TABLE IF EXISTS public.refresh_tokens
                    OWNER to %s;
                ''' % str(self.user)
            )
            cursor.execute(
                '''
                CREATE TABLE public.books
                (
                    id uuid NOT NULL,
                    title text NOT NULL,
                    author text NOT NULL,
                    isbn text NOT NULL,
                    PRIMARY KEY (id)
                );
    
                ALTER TABLE IF EXISTS public.books
                    OWNER to %s;
                ''' % str(self.user)
            )
            connection.autocommit = False

            BooksDBOps.add_book(
                title='Простой Python. Современный стиль программирования. 2-е изд.',
                author='Любанович Б.',
                isbn='978-5-4461-1639-3'
            )

            BooksDBOps.add_book(
                title='FastAPI: веб-разработка на Python',
                author='Любанович Б.',
                isbn='978-601-08-3847-5'
            )

            connection.close()

