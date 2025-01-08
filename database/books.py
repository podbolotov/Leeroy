import uuid
from database.connect_database import create_db_connection


class BooksDatabaseOperations:
    """
    Данный класс включает в себя CRUD-операции над книгами в БД
    """

    @staticmethod
    def add_book(title, author, isbn):
        insert_book_query = """ INSERT INTO public.books (id, title, author, isbn) VALUES (%s,%s,%s,%s) """
        book_id = str(uuid.uuid4())
        book_bundle = (book_id, title, author, isbn)

        connection = create_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(insert_book_query, book_bundle)
            connection.commit()
        connection.close()
        return book_id

    @staticmethod
    def get_all_books():
        connection = create_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * from public.books;')
            books = cursor.fetchall()
        connection.close()
        return books

    @staticmethod
    def get_book_by_id(book_id: uuid.UUID):
        connection = create_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * from public.books WHERE id = %s;', (str(book_id),))
                book = cursor.fetchone()
            connection.close()
            return book
        except Exception as e:
            connection.rollback()
            raise RuntimeError(f'Database request is failed!\n{e}')

    @staticmethod
    def get_book_by_isbn(isbn: str):
        connection = create_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * from public.books WHERE isbn = %s;', (str(isbn),))
                book = cursor.fetchone()
            connection.close()
            if book is not None:
                return book
            else:
                return None
        except Exception as e:
            connection.rollback()
            raise RuntimeError(f'Database request is failed!\n{e}')

    @staticmethod
    def delete_book_by_id(book_id: uuid.UUID):
        connection = create_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('DELETE from public.books WHERE id = %s;', (str(book_id),))
                connection.commit()
            connection.close()
        except Exception as e:
            connection.rollback()
            connection.close()
            raise RuntimeError(f'Database request is failed!\n{e}')