from uuid import UUID

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from database.books import BooksDatabaseOperations as BooksDBOps
from database.users import UsersDatabaseOperations as UsersDBOps
from models.books import CreateBookSuccessfulResponse, CreateBookRequestBody, CreateBookForbiddenError, \
    CreateBookNotUniqueIsbnError


class BooksController:

    @staticmethod
    def create_book(requester_decoded_access_token, request_body = CreateBookRequestBody):

        # Извлекаем ID пользователя, запросившего создание новой книги.
        requester_id = requester_decoded_access_token.user_id

        # Получаем все данные по запрашивающему из БД
        requester_data = UsersDBOps.get_user_data(
            find_by='id',
            user_id=requester_id
        )
        # Проверяем наличие признака "администратор" у запрашивающего пользователя.
        if requester_data.is_admin is False:
            return JSONResponse(
                status_code=403,
                content=jsonable_encoder(
                    CreateBookForbiddenError()
                ))

        is_isbn_used = BooksDBOps.get_book_by_isbn(
            isbn=request_body.isbn
        )

        if is_isbn_used is not None:
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(
                    CreateBookNotUniqueIsbnError(
                        description=f"Book with ISBN {request_body.isbn} already exist")
                ))

        created_book_id = BooksDBOps.add_book(
            title=request_body.title,
            author=request_body.author,
            isbn=request_body.isbn
        )

        return JSONResponse(
            status_code=200,
            content=jsonable_encoder(
                CreateBookSuccessfulResponse(book_id=created_book_id)
            ))


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
