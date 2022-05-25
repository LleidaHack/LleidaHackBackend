class PostgresTable():
    TABLES=[]
    def __init__(self,name,desc) :
        self.name=name
        self.desc=desc
    def get_name(self):
        return self.name
    def get_desc(self):
        return self.desc
    def get_create(self):
        return "CREATE TABLE %s (%s);" % (self.name, self.desc)
    def get_drop(self):
        return "DROP TABLE IF EXISTS %s CASCADE;" % self.name

# USER_TABLE=PostgresTable("users", "user_id serial PRIMARY KEY, user_name text, user_password text, user_email text, user_phone text, user_role text, user_status int")
# EVENT_TABLE="CREATE TABLE events (event_id serial PRIMARY KEY, event_name text, event_date date, event_time time, event_location text, event_description text, event_status int)"

PostgresTable.TABLES.append(PostgresTable("Users", "id serial,name varchar(30) NOT NULL,nickname varchar(20),email varchar(30),password varchar(50),birthday date NOT NULL,phone_number varchar(20),food_restrictions varchar(300),shirt_size varchar(6),constraint pk_users PRIMARY KEY (id);"))
PostgresTable.TABLES.append(PostgresTable("Hacker", "id serial constraint pk_hacker Primary Key, github varchar(100),linkedIn varchar(100),banned boolean,constraint fk_hacker Foreign Key(id) references Users(id);"))
PostgresTable.TABLES.append(PostgresTable("lleida_hacker", "id serial constraint pk_lleida_hacker Primary Key,NIF varchar(9) unique not null,student boolean,active boolean,image bytea,constraint fk_lleida_hacker Foreign Key(id) References Users(id);"))
PostgresTable.TABLES.append(PostgresTable("llhk_group", "id serial constraint pk_llhk_group Primary Key,name varchar(30),description varchar(300);"))
PostgresTable.TABLES.append(PostgresTable("assigned_group", "group_id serial,user_id serial,constraint pk_assigned_group primary key(group_id, user_id),constraint fk_assigned_group_id foreign Key(group_id) references llhk_group(id),constraint fk_assigned_group_user_id foreign key(user_id) references Users(id) ;"))
PostgresTable.TABLES.append(PostgresTable("llhk_Event", "id serial constraint pk_llhk_event primary key,name varchar,description varchar,location varchar,archieved boolean,status varchar,datini date,datfin date;"))
PostgresTable.TABLES.append(PostgresTable("company", "id serial constraint pk_company primary key,phone_number varchar(30),email varchar(100),name varchar(100),nif varchar(100) unique,logo bytea;"))
PostgresTable.TABLES.append(PostgresTable("Address", "id serial constraint pk_address primary Key,street varchar(100),city varchar(50),postal_code varchar(50),country varchar(50);"))
PostgresTable.TABLES.append(PostgresTable("lives_at", "user_id serial,address_id serial,constraint pk_lives_at Primary Key (user_id, address_id),constraint pk_user_lives Foreign Key (user_id) references Users(id),constraint pk_address_lives Foreign key (address_id) references Address(id);"))
PostgresTable.TABLES.append(PostgresTable("Hacker_group", "id serial constraint pk_hacker_group primary Key,name varchar(30),description varchar(200);"))
PostgresTable.TABLES.append(PostgresTable("shift", "id serial constraint pk_shift primary key,datini date,datfin date;"))
PostgresTable.TABLES.append(PostgresTable("organizes", "user_id serial,event_id serial,shift_id serial,constraint pk_organizes primary Key(user_id, event_id),constraint fk_organizes_user foreign key(user_id) references Users(id),constraint fk_organizes_event foreign key(event_id) references llhk_Event(id),constraint fk_organizes_shift foreign key(shift_id) references shift(id);"))
PostgresTable.TABLES.append(PostgresTable("takes_part", "user_id serial,group_id serial,event_id serial,group_position varchar,devpost varchar(500),constraint pk_takes_part primary Key (user_id, group_id, event_id),constraint fk_hacker_takes_part foreign key(user_id) references Users(id),constraint fk_event_takes_part foreign key(event_id) references llhk_Event(id),constraint fk_group_takes_part foreign key(group_id) references Hacker_group(id);"))
PostgresTable.TABLES.append(PostgresTable("sponsors", "company_id serial,event_id serial,description varchar(300),constraint pk_sponsors primary Key(company_id, event_id),constraint fk_sponsors_event foreign Key(event_id) references llhk_Event(id),constraint fk_company_event foreign Key(company_id) references company(id);"))