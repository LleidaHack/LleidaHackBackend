import postgresql
url="pq://user:password@host/name_of_database"
db = postgresql.open(url)

USER_TABLE="CREATE TABLE users (user_id serial PRIMARY KEY, user_name text, user_password text, user_email text, user_phone text, user_role text, user_status int)"
EVENT_TABLE="CREATE TABLE events (event_id serial PRIMARY KEY, event_name text, event_date date, event_time time, event_location text, event_description text, event_status int)"

TABLES=[USER_TABLE, EVENT_TABLE]

def cretaeTables():
    for t in TABLES:
        db.execute(t)
    # db.execute("CREATE TABLE emp (emp_name text PRIMARY KEY, emp_salary numeric)")

def execute_query(query):
    db.execute(query)