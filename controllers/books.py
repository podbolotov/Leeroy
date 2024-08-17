from uuid import UUID
from fastapi.responses import JSONResponse
from database.books import BooksDatabaseOperations as BooksDBOps


class BooksController:
    def __init__(self, connection, cursor):
        self.connection = connection
        self.cursor = cursor

    def get_all_books(self):
        books = BooksDBOps.get_all_books(cursor=self.cursor)
        books_list = []
        for book in books:
            book_dict = {
                "id": book[0],
                "title": book[1],
                "author": book[2],
                "isbn": book[3]
            }
            books_list.append(book_dict)

        return JSONResponse(
            status_code=200,
            content=books_list
        )

    def get_book_by_id(self, book_id: UUID):
        book = BooksDBOps.get_book_by_id(connection=self.connection, cursor=self.cursor, book_id=book_id)
        if book:
            return JSONResponse(
                status_code=200,
                content={
                    "id": book[0],
                    "title": book[1],
                    "author": book[2],
                    "isbn": book[3]
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "NOT_FOUND",
                    "description": f"Book with ID {book_id} is not found"
                })
