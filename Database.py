import os
from os.path import exists

from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import Error, sql
import psycopg2


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

    def show_tables(self):
        SQL = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"""
        return self.execute_query(query=SQL, fetchAll=True)

    def show_columns(self, table_name):
        SQL = "SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
        parameters=(table_name,)
        return [x[0] for x in self.execute_query(query=SQL, parameters=parameters, fetchAll=True)]


    def read_table(self, table_name):
        SQL = f"SELECT * from {table_name};"
        return self.execute_query(query=SQL, fetchAll=True)

    def create_table(self, table_name, columns):
        columns = ", ".join(columns)
        SQL = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        return self.execute_query(query=SQL, commit=True)

    def get_row_by_id(self, cursor, id, table_name):
        SQL = "SELECT * from %(table_name)s where id = %(id)s;"
        parameters = {'table_name': table_name, 'id': id}
        query = cursor.execute(query=SQL, parameters=parameters)
        return query.fetchOne()

    def delete_row_by_id(self, table_name, id):
        SQL = f"DELETE from {table_name} where id = {id};"
        # parameters = (table_name, id)
        self.execute_query(query=SQL, commit=True)

    def verify_password(self, email, pwd):
        retrieved_password = self.execute_query(query="SELECT value FROM settings where key = %s;", parameters=(email,),
                                                fetchOne=True)
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
        self.execute_query(query=SQL, parameters=parameters, commit=True)


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
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Investment(Main):
    def __init__(self, english, korean, min_price, max_price):
        self.english = english
        self.korean = korean
        self.min_price = min_price
        self.max_price = max_price

    def register_investment(self):
        SQL = "INSERT INTO investments (english, korean, min_price, max_price) VALUES (%s,%s,%s,%s);"
        parameters = (self.english, self.korean, self.min_price, self.max_price,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_investment(self, id):
        SQL = "UPDATE investments SET english = %s, korean = %s, min_price = %s, max_price = %s WHERE id = %s;"
        parameters = (self.english, self.korean, self.min_price, self.max_price, id)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class FixedCost(Main):
    def __init__(self, english_name, korean_name, cost_per_month, one_time_cost, period_months):
        self.english_name = english_name
        self.korean_name = korean_name
        self.cost_per_month = cost_per_month
        self.one_time_cost = one_time_cost
        self.period_months = period_months

    def register_cost(self):
        SQL = "INSERT INTO fixed_costs (english_name, korean_name, cost_per_month, one_time_cost, period_months) VALUES (%s,%s,%s,%s,%s);"
        parameters = (self.english_name, self.korean_name, self.cost_per_month, self.one_time_cost, self.period_months,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_cost(self, id):
        SQL = "UPDATE fixed_costs SET english_name = %s, korean_name = %s, cost_per_month = %s, one_time_cost = %s, period_months = %s WHERE id = %s;"
        parameters = (
        self.english_name, self.korean_name, self.cost_per_month, self.one_time_cost, self.period_months, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class VariableCost(Main):
    def __init__(self, english, korean, variable_cost, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv,
                 selling_price_hv, criteria_hv, unit, work_time_min, image):
        self.english = english
        self.korean = korean
        self.variable_cost = variable_cost
        self.selling_price_lv = selling_price_lv
        self.criteria_lv = criteria_lv
        self.selling_price_mv = selling_price_mv
        self.criteria_mv = criteria_mv
        self.selling_price_hv = selling_price_hv
        self.criteria_hv = criteria_hv
        self.unit = unit
        self.work_time_min = work_time_min
        self.image = image

    def register_cost(self):
        SQL = "INSERT INTO variable_costs (english, korean, variable_cost, selling_price_lv, criteria_lv,selling_price_mv, criteria_mv,selling_price_hv, criteria_hv,unit, work_time_min, image) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
        self.english, self.korean, self.variable_cost, self.selling_price_lv, self.criteria_lv, self.selling_price_mv,
        self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.unit, self.work_time_min, self.image,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_cost(self, id):
        SQL = "UPDATE variable_costs SET english = %s, korean = %s, variable_cost = %s, selling_price_lv = %s, criteria_lv = %s, selling_price_mv = %s, criteria_mv = %s, selling_price_hv = %s, criteria_hv = %s, unit = %s, work_time_min = %s, image = %s WHERE id = %s;"
        parameters = (
        self.english, self.korean, self.variable_cost, self.selling_price_lv, self.criteria_lv, self.selling_price_mv,
        self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.unit, self.work_time_min, self.image, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Comment(Main):
    def __init__(self, name):
        self.name = name

    def register_comment(self):
        SQL = "INSERT INTO comments (comment) VALUES (%s);"
        parameters = (self.name,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)
