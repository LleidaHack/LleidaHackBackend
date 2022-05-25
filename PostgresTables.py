from __future__ import annotations
class PostgresTable():
    TABLES={}
    def __init__(self,name,desc) -> PostgresTable:
        self.name=name
        self.desc=desc
        self.params=[]
        #extract sql params from table description
        for i in desc.split(','):
            name=i.split(' ')[0]
            if not name =="constraint":
                self.params.append(name)
    def get_name(self):
        return self.name
    def get_desc(self):
        return self.desc
    def get_create(self):
        return "CREATE TABLE %s (%s);" % (self.name, self.desc)
    def get_drop(self):
        return "DROP TABLE IF EXISTS %s CASCADE;" % self.name
    def get_insert(self):
        return "INSERT INTO %s (%s) VALUES (%s);" % (self.name,','.join(self.params),','.join(['%s']*len(self.params)))
    def get_select(self):
        return "SELECT * FROM %s;" % self.name
    # def get_update(self):
        # return "UPDATE %s SET %s WHERE %s;" % (self.name,','.join(self.params),self.params[0])
    # def get_delete(self):
        # return "DELETE FROM %s WHERE %s;" % (self.name,self.params[0])
    @staticmethod
    def add_table(table) -> PostgresTable:
        PostgresTable.TABLES[table.get_name()]=table
    @staticmethod
    def get_table(name) -> PostgresTable:
        return PostgresTable.TABLES[name]


PostgresTable.add_table(PostgresTable("llhk_user", "id serial,name varchar(30) NOT NULL,nickname varchar(20),email varchar(30),password varchar(50),birthday date NOT NULL,phone_number varchar(20),food_restrictions varchar(300),shirt_size varchar(6),constraint pk_llhk_user PRIMARY KEY (id)"))
PostgresTable.add_table(PostgresTable("Hacker", "id serial constraint pk_hacker Primary Key, github varchar(100),linkedIn varchar(100),banned boolean,constraint fk_hacker Foreign Key(id) references llhk_user(id)"))
PostgresTable.add_table(PostgresTable("lleida_hacker", "id serial constraint pk_lleida_hacker Primary Key,NIF varchar(9) unique not null,student boolean,active boolean,image bytea,constraint fk_lleida_hacker Foreign Key(id) References llhk_user(id)"))
PostgresTable.add_table(PostgresTable("llhk_group", "id serial constraint pk_llhk_group Primary Key,name varchar(30),description varchar(300)"))
PostgresTable.add_table(PostgresTable("assigned_group", "group_id serial,user_id serial,constraint pk_assigned_group primary key(group_id, user_id),constraint fk_assigned_group_id foreign Key(group_id) references llhk_group(id),constraint fk_assigned_group_user_id foreign key(user_id) references llhk_user(id) "))
PostgresTable.add_table(PostgresTable("llhk_Event", "id serial constraint pk_llhk_event primary key,name varchar,description varchar,location varchar,archieved boolean,status varchar,datini date,datfin date"))
PostgresTable.add_table(PostgresTable("company", "id serial constraint pk_company primary key,phone_number varchar(30),email varchar(100),name varchar(100),nif varchar(100) unique,logo bytea"))
PostgresTable.add_table(PostgresTable("Address", "id serial constraint pk_address primary Key,street varchar(100),city varchar(50),postal_code varchar(50),country varchar(50)"))
PostgresTable.add_table(PostgresTable("lives_at", "user_id serial,address_id serial,constraint pk_lives_at Primary Key (user_id, address_id),constraint pk_user_lives Foreign Key (user_id) references llhk_user(id),constraint pk_address_lives Foreign key (address_id) references Address(id)"))
PostgresTable.add_table(PostgresTable("Hacker_group", "id serial constraint pk_hacker_group primary Key,name varchar(30),description varchar(200)"))
PostgresTable.add_table(PostgresTable("shift", "id serial constraint pk_shift primary key,datini date,datfin date"))
PostgresTable.add_table(PostgresTable("organizes", "user_id serial,event_id serial,shift_id serial,constraint pk_organizes primary Key(user_id, event_id),constraint fk_organizes_user foreign key(user_id) references llhk_user(id),constraint fk_organizes_event foreign key(event_id) references llhk_Event(id),constraint fk_organizes_shift foreign key(shift_id) references shift(id)"))
PostgresTable.add_table(PostgresTable("takes_part", "user_id serial,group_id serial,event_id serial,group_position varchar,devpost varchar(500),constraint pk_takes_part primary Key (user_id, group_id, event_id),constraint fk_hacker_takes_part foreign key(user_id) references llhk_user(id),constraint fk_event_takes_part foreign key(event_id) references llhk_Event(id),constraint fk_group_takes_part foreign key(group_id) references Hacker_group(id)"))
PostgresTable.add_table(PostgresTable("sponsors", "company_id serial,event_id serial,description varchar(300),constraint pk_sponsors primary Key(company_id, event_id),constraint fk_sponsors_event foreign Key(event_id) references llhk_Event(id),constraint fk_company_event foreign Key(company_id) references company(id)"))

# print(PostgresTable.TABLES["llhk_user"].params)