import os
from os.path import exists

from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import Error, sql
import psycopg2
from functools import wraps




class Main:
    """
        This main class of the database helper is:
            - to execute all types of queries
            - read a table in the database
            - delete an entry in a table in the database
    """

    def execute_query(self, query, parameters=(), commit=False, fetchAll=False, fetchOne=False):
        try:
            if exists('database_credentials.txt'):
                credentials = str(open("database_credentials.txt", 'r').read())
                conn = psycopg2.connect(credentials, sslmode='require')
            else:
                DATABASE_URL = os.environ['DATABASE_URL']
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')

            c = conn.cursor()
            result = None
            c.execute(query, parameters)
            if commit:
                conn.commit()
            if fetchAll:
                result = [row for row in c.fetchall()]
            if fetchOne:
                result = c.fetchone()[0]
            c.close()
            conn.close()
            return result

        except Error as e:
            print(e)


    def read_table(self, cursor, table_name):
        SQL = "SELECT * from %(table_name)s"
        parameters = {'table_name': table_name}
        query = cursor.execute(query=SQL, variables=parameters)
        return query.fetchall()

    def get_row_by_id(self, cursor, id, table_name):
        SQL = "SELECT * from %(table_name)s where id = %(id)s"
        parameters = {'table_name': table_name, 'id': id}
        query = cursor.execute(query=SQL, variables=parameters)
        return query.fetchOne()

    def verify_password(self, email, pwd):
        retrieved_password = self.execute_query(query="SELECT value FROM settings where key = %s;", parameters=(email,), fetchOne=True)
        return check_password_hash(retrieved_password, pwd)

    def get_secret_code(self):
        retrieved_code = self.execute_query(query="SELECT value FROM settings where id=1 ;", fetchOne=True)
        return retrieved_code


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
        SQL = "INSERT INTO contact_query (first_name, last_name, nickname, password, role_name, email, last_login) VALUES (%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
        self.first_name, self.last_name, self.nickname, self.password, self.role_name, self.email, self.last_login)
        self.execute_query(query=SQL, variables=parameters, commit=True)


class Contact(Main):
    def __init__(self, name, message, date, reason, phone, email, address):
        self.name = name
        self.message = message
        self.date = date
        self.reason = reason
        self.phone = phone
        self.email = email
        self.address = address

    def register_contact_query(self):
        SQL = "INSERT INTO contact_query (name, message, date, reason, phone, email, address) VALUES (%s,%s,%s,%s,%s,%s,%s);"
        parameters = (self.name, self.message, self.date, self.reason, self.phone, self.email, self.address,)
        self.execute_query(query=SQL, variables=parameters, commit=True)
