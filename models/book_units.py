from pydantic import BaseModel
from models.default_error import DefaultError

class BookUnitHasActualReservationsError(DefaultError):
    """ Данная ошибка возвращается в случае, если у книги запрошенной к удалению имеются забронированные (выданные
    читателям) экземпляры. """
    status: str = "FORBIDDEN"
    description: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "FORBIDDEN",
                    "description": "Book with ID 47d9ba5e-7a97-473f-850a-65c422e32279 has actual reservations and "
                                   "cannot be deleted"
                }
            ]
        }
    }