import psycopg2
from configparser import ConfigParser

from DBConnector import DBConnector
from PostgresTables import PostgresTable



class PostgresConnector(DBConnector):
    def __init__(self,file: str ='database.ini') -> None:
        super().__init__()
        self.config = ConfigParser()
        self.config.read(file)
        self.db_name = self.config['postgres']['database']
        self.user = self.config['postgres']['user']
        self.password = self.config['postgres']['password']
        self.host = self.config['postgres']['host']
        self.port = self.config['postgres']['port']
        self.recreate_tables = self.config['postgres']['recreate_tables']
        self.conn = None
        self.cursor = None
        self.connect()
        if self.recreate_tables == 'True':
            self.dropTables()
            self.cretaeTables()
    
    def connect(self):
        self.conn = psycopg2.connect(database=self.db_name, user=self.user, password=self.password, host=self.host, port=self.port)
        self.cursor = self.conn.cursor()

    def cretaeTables(self):
        for t in PostgresTable.TABLES: 
            self.cursor.execute(t.get_create())
        self.commit()

    def dropTables(self):
        for t in PostgresTable.TABLES:
            self.cursor.execute(t.get_drop())
        self.commit()
    
    def insert(self,query:str,params):
        self.cursor.execute(query,params)
        self.commit()
    
    # def update(self,query:str,params):
        # self.cursor.execute(query,params)
        # self.commit()

    async def select(self,query:str,params=()):
        self.cursor.execute(query,params)
        return await self.cursor.fetchall()

    def commit(self):
        self.conn.commit()
        self.cursor.close()
        self.cursor=self.conn.cursor()

    def abort(self):
        self.conn.abort()
        self.cursor.close()
        self.cursor=self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()
