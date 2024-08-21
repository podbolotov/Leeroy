import psycopg2
import uuid
from data.users import DefaultAdministrator
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
        self.connection = None
        self.cursor = None
        self.user = str(SeVars.DB_USER)
        self.password = str(SeVars.DB_PASSWORD)
        self.host = str(SeVars.DB_HOST)
        self.port = str(SeVars.DB_PORT)

    def connect_to_database(self):
        # Первым шагом происходит подключение к стандартной базе данных "postgres". Это необходимо для проверки
        # существования базы данных приложения "leeroy".
        self.connection = psycopg2.connect(
            dbname='postgres', user=self.user, password=self.password, host=self.host, port=self.port
        )
        # Создаём курсор
        self.cursor = self.connection.cursor()
        # Проверяем существование базы данных "leeroy".
        self.cursor.execute('SELECT datname FROM pg_database WHERE datname = \'leeroy\'')
        leeroy_in_exist = self.cursor.fetchone()

        if leeroy_in_exist is None:
            self.create_leeroy_database()
        else:
            print("Leeroy DB is exist. Try to reconnect...")
            self.connection.close()
            self.connection = psycopg2.connect(
                dbname='leeroy', user=self.user, password=self.password, host=self.host, port=self.port
            )
            self.cursor = self.connection.cursor()

        return self.connection, self.cursor

    def create_leeroy_database(self):
        self.connection.rollback()
        self.connection.autocommit = True
        self.cursor.execute(
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
        self.cursor.execute(
            '''
            ALTER DATABASE leeroy SET timezone TO 'UTC';
            '''
        )
        self.connection.close()
        self.connection = psycopg2.connect(
            dbname='leeroy', user=self.user, password=self.password, host=self.host, port=self.port
        )
        self.connection.autocommit = True
        self.cursor = self.connection.cursor()
        print("DB created. Creating tables...")
        self.cursor.execute(
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
            connection=self.connection,
            cursor=self.cursor,
            firstname=DefaultAdministrator.firstname,
            middlename=DefaultAdministrator.middlename,
            surname=DefaultAdministrator.surname,
            email=DefaultAdministrator.email,
            hashed_password=hashed_default_user_password,
            is_admin=DefaultAdministrator.is_admin,
        )

        self.cursor.execute(
            '''
            CREATE TABLE public.access_tokens
            (
                id uuid NOT NULL,
                user_id uuid NOT NULL,
                issued_at timestamp with time zone NOT NULL,
                expired_at timestamp with time zone NOT NULL,
                refresh_token_id uuid NOT NULL,
                revoked boolean NOT NULL DEFAULT false,
                PRIMARY KEY (id)
            );
            
            ALTER TABLE IF EXISTS public.access_tokens
                OWNER to %s;
            ''' % str(self.user)
        )
        self.cursor.execute(
            '''
            CREATE TABLE public.refresh_tokens
            (
                id uuid NOT NULL,
                user_id uuid NOT NULL,
                issued_at timestamp with time zone NOT NULL,
                expired_at timestamp with time zone NOT NULL,
                access_token_id uuid NOT NULL,
                revoked boolean NOT NULL DEFAULT false,
                PRIMARY KEY (id)
            );

            ALTER TABLE IF EXISTS public.refresh_tokens
                OWNER to %s;
            ''' % str(self.user)
        )
        self.cursor.execute(
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
        self.connection.autocommit = False

        BooksDBOps.add_book(
            connection=self.connection,
            cursor=self.cursor,
            title='Простой Python. Современный стиль программирования. 2-е изд.',
            author='Любанович Б.',
            isbn='978-5-4461-1639-3'
        )

        BooksDBOps.add_book(
            connection=self.connection,
            cursor=self.cursor,
            title='FastAPI: веб-разработка на Python',
            author='Любанович Б.',
            isbn='978-601-08-3847-5'
        )
