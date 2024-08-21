import uuid


class BooksDatabaseOperations:
    """
    Данный класс включает в себя CRUD-операции над книгами в БД
    """

    @staticmethod
    def add_book(connection, cursor, title, author, isbn):
        insert_book_query = """ INSERT INTO public.books (id, title, author, isbn) VALUES (%s,%s,%s,%s) """
        book_id = str(uuid.uuid4())
        book_bundle = (book_id, title, author, isbn)
        cursor.execute(insert_book_query, book_bundle)
        connection.commit()
        return book_id

    @staticmethod
    def get_all_books(cursor):
        cursor.execute('SELECT * from public.books;')
        books = cursor.fetchall()
        return books

    @staticmethod
    def get_book_by_id(connection, cursor, book_id: uuid.UUID):
        try:
            cursor.execute('SELECT * from public.books WHERE id = %s;', (str(book_id),))
            book = cursor.fetchone()
            return book
        except Exception as e:
            connection.rollback()
            raise RuntimeError(f'Database request if failed!\n{e}')
