import psycopg2
from configparser import ConfigParser

url="pq://user:password@host/name_of_database"
db = postgresql.open(url)

USER_TABLE="CREATE TABLE users (user_id serial PRIMARY KEY, user_name text, user_password text, user_email text, user_phone text, user_role text, user_status int)"
EVENT_TABLE="CREATE TABLE events (event_id serial PRIMARY KEY, event_name text, event_date date, event_time time, event_location text, event_description text, event_status int)"

TABLES=[USER_TABLE, EVENT_TABLE]

def connect():
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

def cretaeTables():
    for t in TABLES:
        db.execute(t)
    # db.execute("CREATE TABLE emp (emp_name text PRIMARY KEY, emp_salary numeric)")

def execute_query(query):
    db.execute(query)

#!/usr/bin/python


def config(filename='database.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db