import psycopg2
from data.service_variables import ServiceVariables as SeVars

def create_db_connection(target: str = 'leeroy'):
    connection = psycopg2.connect(
        dbname=target,
        user=str(SeVars.DB_USER),
        password=str(SeVars.DB_PASSWORD),
        host=str(SeVars.DB_HOST),
        port=str(SeVars.DB_PORT)
    )
    return connection