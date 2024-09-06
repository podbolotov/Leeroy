from uuid import UUID
from fastapi.responses import JSONResponse
from database.books import BooksDatabaseOperations as BooksDBOps


class BooksController:

    @staticmethod
    def get_all_books():
        books = BooksDBOps.get_all_books()
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

    @staticmethod
    def get_book_by_id(book_id: UUID):
        book = BooksDBOps.get_book_by_id(book_id=book_id)
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
