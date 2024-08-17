from os import environ


class ServiceVariables:
    """
    Данный класс предсталвяет собой централизованное хранилище ссылок на переменные окружения,
    а также на их значения по умолчанию, если они не были определены в оболочке.
    """
    DB_HOST = environ.get('DB_HOST') or '127.0.0.1'
    ''' IP адрес СУБД '''

    DB_PORT = environ.get('DB_PORT') or '5432'
    ''' Порт, на который СУБД принимает подключения '''

    DB_USER = environ.get('DB_USER') or 'postgres'
    ''' Имя пользователя, от имени которого будет происходить подключение к СУБД '''

    DB_PASSWORD = environ.get('DB_PASSWORD') or 'postgres'
    ''' Пароль пользователя, от имени которого будет происходить подключение к СУБД '''

    PASSWORD_HASH_SALT = environ.get('PASSWORD_HASH_SALT') or "DefaultPasswordHashSalt"
    ''' Соль, применяемая при хэшировании паролей пользователей '''

    JWT_SIGNATURE_SECRET = environ.get('JWT_SIGNATURE_SECRET') or "DefaultJSONWebTokenSignatureSecret"
    ''' Секрет для подписи генерируемых JWT '''

    ACCESS_TOKEN_TTL_IN_MINUTES = environ.get('ACCESS_TOKEN_TTL_IN_MINUTES') or 60
    ''' Время жизни генерируемых токенов доступа (в минутах) '''

    REFRESH_TOKEN_TTL_IN_MINUTES = environ.get('REFRESH_TOKEN_TTL_IN_MINUTES') or 43200
    ''' Время жизни генерируемых токенов обновления (в минутах) '''
