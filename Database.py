from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import Error
import psycopg2


class Main:
    """
        This main class of the database helper is:
            - to execute all types of queries
            - read a table in the database
            - delete an entry in a table in the database
    """

    def execute_query(self, query_list, commit=False, fetchAll=False, fetchOne=False):
        try:
            credentials = str(open("database_credentials.txt", 'r').read())
            conn = psycopg2.connect(credentials, sslmode='require')
            c = conn.cursor()
            result = None
            if type(query_list) == str:
                c.execute(query_list)
            elif isinstance(query_list, tuple):
                c.execute(query_list[0], query_list[1])
            else:
                for query in query_list:
                    if isinstance(query, tuple):
                        c.execute(query[0], query[1])
                    else:
                        c.execute(query)
            if commit:
                conn.commit()
            if fetchAll:
                result = [row for row in c.fetchall()]
            if fetchOne:
                result = c.fetchone()
            c.close()
            conn.close()
            return result

        except Error as e:
            print(e)

    def read_table(self, table_name):
        return self.execute_query(query_list=f"SELECT * FROM {table_name}", fetchAll=True)

    def read_columns(self, db_name):
        return self.execute_query(
            "SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '" + db_name + "';", fetchAll=True)

    def del_comment(self, id, db_name):
        self.execute_query(query_list=f'DELETE FROM {db_name} WHERE id = {id}', commit=True)

    def add_column(self, table_name, new_column_name, column_definition):
        self.execute_query(f"ALTER TABLE {table_name} ADD {new_column_name} {column_definition};", commit=True)

    def verify_password(self, email, pwd):
        retrieved_password = \
            self.execute_query(query_list=f"SELECT password FROM users where email = '{email}'", fetchAll=True)[0][0]
        return check_password_hash(retrieved_password, pwd)

    def verify_admin(self, email):
        role = self.execute_query(query_list=f"SELECT role_name FROM users where email = '{email}'", fetchAll=True)[0][
            0]
        if role == "Administrator":
            return True
        else:
            return False

    def generate_hash(self, pwd):
        return generate_password_hash(pwd)

    def get_user_id(self, email):
        return self.execute_query(query_list=f"SELECT ID from users where email = '{email}'", fetchOne=True)[0]

    def get_user_email(self, id):
        global email
        try:
            email = self.execute_query(query_list=f"SELECT email from users where id = '{id}'", fetchOne=True)[0]
        except TypeError as e:
            email = None
        finally:
            return email

    def get_user_data(self, id):
        return self.execute_query(query_list=f"SELECT * from users where id = '{id}'", fetchAll=True)[0]

    def update_last_login(self, id):
        self.execute_query(query_list=F"UPDATE users SET last_login = NOW() where id = {id}", commit=True)

    def alter_password(self, email, old_pwd, new_pwd):
        # "23FvMIs*5cx8fHRv"
        new_pwd = generate_password_hash(new_pwd)
        if self.verify_password(email, old_pwd):
            self.execute_query(query_list=f"UPDATE users SET password = '{new_pwd}' where email = '{email}'",
                               commit=True)
            return True
        else:
            return False


class User(Main):
    def __init__(self, nickname, password, role, first_name, last_name, email, last_login):
        self.first_name = first_name
        self.last_name = last_name
        self.nickname = nickname
        self.password = generate_password_hash(password)
        self.role_name = role
        self.email = email
        self.last_login = last_login

    def register_user(self):
        self.execute_query(
            query_list=f"INSERT INTO users (first_name, last_name, nickname, password, role, email, last_login, created_on) VALUES ({self.first_name}, {self.last_name}, {self.nickname}, {self.password}, {self.role_name}, {self.email}, NOW(), NOW());",
            commit=True)

