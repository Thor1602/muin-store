import os
from os.path import exists

from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import Error, sql
import psycopg2

import googledrive_connector


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
        parameters = (table_name,)
        return [x[0] for x in self.execute_query(query=SQL, parameters=parameters, fetchAll=True)]

    def read_table(self, table_name, order_asc="", order_desc=""):
        argument = ""
        if order_asc != "":
            argument = f"order by {order_asc} asc"
        if order_desc != "":
            argument = f"order by {order_desc} desc"
        SQL = f"SELECT * from {table_name} {argument};"
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

    def fetch_variable_costs(self):
        col = ('cost_id', 'english', 'korean', 'variable_cost', 'selling_price_lv', 'criteria_lv', 'selling_price_mv',
               'criteria_mv', 'selling_price_hv', 'criteria_hv', 'unit', 'work_time_min', 'estimated_items',
               'product_ID')
        SQL = "SELECT variable_costs.id, english, korean, variable_cost, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv, selling_price_hv, criteria_hv, unit, work_time_min, estimated_items, productid FROM products JOIN variable_costs ON variable_costs.productID = products.id;"
        return (self.execute_query(SQL, fetchAll=True), col)

    def add_setting(self, name, key, value):
        self.execute_query("INSERT INTO settings (name, key, value) VALUES (%s,%s,%s)",
                           (name, key, value,), commit=True)

    def add_column(self, tablename, columname, type, default_value=None):
        self.execute_query(f"ALTER TABLE {tablename} ADD COLUMN {columname} {type} DEFAULT '{default_value}';",
                           commit=True)
        # main.add_column(tablename='products', columname='type', type='VARCHAR', default_value='pastry')

    def get_setting_by_name(self, name):
        return \
            self.execute_query(query="SELECT key, value FROM settings where name = '{}';".format(name), fetchAll=True)[
                0]

    def get_cloud_images(self):
        return googledrive_connector.list_all_files(parent='images')

    def get_membership_points(self, phone_number):
        SQL = "SELECT points from memberships where phone_number = %(phone_number)s;"
        parameters = {'phone_number': phone_number}
        query = self.execute_query(query=SQL, parameters=parameters, fetchOne=True)
        return query

    def phone_number_exists(self, phone_number):
        SQL = "SELECT phone_number from memberships;"
        query = self.execute_query(query=SQL, fetchAll=True)
        if phone_number in [x[0] for x in query]:
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
        SQL = "INSERT INTO user (first_name, last_name, nickname, password, role_name, email, last_login) VALUES (%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.first_name, self.last_name, self.nickname, self.password, self.role_name, self.email, self.last_login)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Membership(Main):
    def __init__(self, first_name, last_name, phone_number, points):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.points = points

    def register(self):
        SQL = "INSERT INTO memberships (first_name, last_name, phone_number, points) VALUES (%s,%s,%s,%s);"
        parameters = (self.first_name, self.last_name, self.phone_number, self.points,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_points(self, inserted_phone_number, points_of_current_sale):
        query = "SELECT points from memberships where phone_number = %(phone_number)s;"
        parameters = {'phone_number': inserted_phone_number}
        collected_points = self.execute_query(query=query, parameters=parameters, fetchOne=True)
        collected_points += points_of_current_sale
        SQL = "UPDATE memberships SET points = %s WHERE phone_number = %s;"
        parameters = (
            collected_points, self.phone_number, inserted_phone_number,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Contact(Main):
    def __init__(self, name, email, address, phone, subject, message):
        self.name = name
        self.email = email
        self.address = address
        self.phone = phone
        self.subject = subject
        self.message = message

    def register_contact_query(self):
        SQL = "INSERT INTO customer_contact_submission (name, email, address, phone, subject, message, time, isrepliedto) VALUES (%s,%s,%s,%s,%s,%s,now()::timestamp, FALSE);"
        parameters = (self.name, self.email, self.address, self.phone, self.subject, self.message)
        self.execute_query(query=SQL, parameters=parameters, commit=True)
    def isRead(self, id):
        SQL = "UPDATE customer_contact_submission SET isrepliedto = TRUE WHERE id = %s;"
        parameters = (id,)
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
    def __init__(self, productid, variable_cost, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv,
                 selling_price_hv, criteria_hv, work_time_min, estimated_items):
        self.productid = productid
        self.variable_cost = variable_cost
        self.selling_price_lv = selling_price_lv
        self.criteria_lv = criteria_lv
        self.selling_price_mv = selling_price_mv
        self.criteria_mv = criteria_mv
        self.selling_price_hv = selling_price_hv
        self.criteria_hv = criteria_hv
        self.work_time_min = work_time_min
        self.estimated_items = estimated_items

    def register_cost(self):
        SQL = "INSERT INTO variable_costs (productid, variable_cost, selling_price_lv, criteria_lv,selling_price_mv, criteria_mv,selling_price_hv, criteria_hv, work_time_min, estimated_items) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.productid, self.variable_cost, self.selling_price_lv, self.criteria_lv, self.selling_price_mv,
            self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.work_time_min,
            self.estimated_items,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_cost(self, id):
        SQL = "UPDATE variable_costs SET productid = %s, variable_cost = %s, selling_price_lv = %s, criteria_lv = %s, selling_price_mv = %s, criteria_mv = %s, selling_price_hv = %s, criteria_hv = %s, work_time_min = %s, estimated_items = %s WHERE id = %s;"
        parameters = (
            self.productid, self.variable_cost, self.selling_price_lv, self.criteria_lv,
            self.selling_price_mv,
            self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.work_time_min,
            self.estimated_items, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Comment(Main):
    def __init__(self, name):
        self.name = name

    def register_comment(self):
        SQL = "INSERT INTO comments (comment) VALUES (%s);"
        parameters = (self.name,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Ingredients(Main):
    def __init__(self, english, korean):
        self.english = english
        self.korean = korean

    def register_ingredient(self):
        SQL = "INSERT INTO ingredients (english, korean) VALUES (%s,%s);"
        parameters = (self.english, self.korean,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update_ingredient(self, id):
        SQL = "UPDATE ingredients SET english = %s, korean = %s WHERE id = %s;"
        parameters = (
            self.english, self.korean, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class PricesIngredients(Main):
    def __init__(self, ingredientID, price, weight_in_gram, date=None):
        self.ingredientID = ingredientID
        self.price = price
        self.weight_in_gram = weight_in_gram
        self.date = date

    def register(self):
        if self.date == None:
            SQL = "INSERT INTO prices_ingredients (ingredientid, price, weight_in_gram, date) VALUES (%s,%s,%s,NOW());"
            parameters = (self.ingredientID, self.price, self.weight_in_gram,)
        else:
            SQL = "INSERT INTO prices_ingredients (ingredientid, price, weight_in_gram, date) VALUES (%s,%s,%s,%s);"
            parameters = (self.ingredientID, self.price, self.weight_in_gram, self.date,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        if self.date == None:
            SQL = "UPDATE prices_ingredients SET ingredientID = %s, price = %s, weight_in_gram = %s WHERE id = %s;"
            parameters = (self.ingredientID, self.price, self.weight_in_gram,)
        else:
            SQL = "UPDATE prices_ingredients SET ingredientID = %s, price = %s, weight_in_gram = %s WHERE id = %s;"
            parameters = (self.ingredientID, self.price, self.weight_in_gram, self.date, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Packaging(Main):
    def __init__(self, english, korean):
        self.english = english
        self.korean = korean

    def register(self):
        SQL = "INSERT INTO packaging (english, korean) VALUES (%s,%s);"
        parameters = (self.english, self.korean,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE packaging SET english = %s, korean = %s WHERE id = %s;"
        parameters = (
            self.english, self.korean, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class PricesPackaging(Main):
    def __init__(self, packagingID, price_per_unit, date=None):
        self.packagingID = packagingID
        self.price_per_unit = price_per_unit
        self.date = date

    def register(self):
        if self.date == None:
            SQL = "INSERT INTO prices_packaging (packagingID, price_per_unit,date) VALUES (%s,%s,now());"
            parameters = (self.packagingID, self.price_per_unit,)
        else:
            SQL = "INSERT INTO prices_packaging (packagingID, price_per_unit,date) VALUES (%s,%s,%s);"
            parameters = (self.packagingID, self.price_per_unit, self.date,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        if self.date == None:
            SQL = "UPDATE prices_packaging SET packagingID = %s, price_per_unit = %s WHERE id = %s;"
            parameters = (self.packagingID, self.price_per_unit, id,)
        else:
            SQL = "UPDATE prices_packaging SET packagingID = %s, price_per_unit = %s, date = %s WHERE id = %s;"
            parameters = (self.packagingID, self.price_per_unit, self.date, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class Products(Main):
    def __init__(self, english, korean, weight_in_gram_per_product, unit, image, type, currently_selling, best, Korean_description, English_description, QR):
        self.english = english
        self.korean = korean
        self.weight_in_gram_per_product = weight_in_gram_per_product
        self.unit = unit
        self.image = image
        self.type = type
        self.currently_selling = currently_selling
        self.best = best
        self.Korean_description = Korean_description
        self.English_description = English_description
        self.QR = QR

    def register(self):
        SQL = "INSERT INTO products (english, korean, weight_in_gram_per_product, unit ,image,type,currently_selling, best, Korean_description, English_description, QR) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        parameters = (self.english, self.korean, self.weight_in_gram_per_product, self.unit, self.image, self.type,
                      self.currently_selling, self.best, self.Korean_description, self.English_description, self.QR,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE products SET english = %s, korean = %s, weight_in_gram_per_product = %s, unit = %s, image = %s , type = %s , currently_selling = %s, best = %s, Korean_description = %s, English_description = %s , QR = %s WHERE id = %s;"
        parameters = (
            self.english, self.korean, self.weight_in_gram_per_product, self.unit, self.image, self.type,
            self.currently_selling, self.best, self.Korean_description, self.English_description, self.QR, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class IngredientProduct(Main):
    def __init__(self, productID, ingredientID, weight_in_gram):
        self.productID = productID
        self.ingredientID = ingredientID
        self.weight_in_gram = weight_in_gram

    def register(self):
        SQL = "INSERT INTO ingredientproduct (productID, ingredientID, weight_in_gram) VALUES (%s,%s,%s);"
        parameters = (self.productID, self.ingredientID, self.weight_in_gram,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE ingredientproduct SET productID = %s, ingredientID = %s, weight_in_gram = %s WHERE id = %s;"
        parameters = (self.productID, self.ingredientID, self.weight_in_gram, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class PackagingProduct(Main):
    def __init__(self, productID, packagingID):
        self.productID = productID
        self.packagingID = packagingID

    def register(self):
        SQL = "INSERT INTO packagingproduct (productID, packagingID) VALUES (%s,%s);"
        parameters = (self.productID, self.packagingID,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE packagingproduct SET productID = %s, packagingID = %s WHERE id = %s;"
        parameters = (self.productID, self.packagingID, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class InvoicesSupplier(Main):
    def __init__(self, file, type, payment_amount, payment_method, supplier_name, invoice_date):
        self.file = file
        self.type = type
        self.payment_amount = payment_amount
        self.payment_method = payment_method
        self.supplier_name = supplier_name
        self.invoice_date = invoice_date

    def register(self):
        SQL = "INSERT INTO invoices_suppliers (file, type, payment_amount, payment_method, supplier_name, invoice_date) VALUES (%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.supplier_name, self.invoice_date,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE invoices_suppliers SET file = %s, type = %s, payment_amount = %s, payment_method = %s, supplier_name = %s , invoice_date = %s WHERE id = %s;"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.supplier_name, self.invoice_date, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class InvoicesCustomer(Main):
    def __init__(self, file, type, payment_amount, payment_method, customer_name, invoice_date):
        self.file = file
        self.type = type
        self.payment_amount = payment_amount
        self.payment_method = payment_method
        self.customer_name = customer_name
        self.invoice_date = invoice_date

    def register(self):
        SQL = "INSERT INTO invoices_customers (file, type, payment_amount, payment_method, customer_name, invoice_date) VALUES (%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.customer_name, self.invoice_date,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE invoices_customers SET file = %s, type = %s, payment_amount = %s, payment_method = %s, customer_name = %s , invoice_date = %s WHERE id = %s;"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.customer_name, self.invoice_date, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class WebTranslations(Main):
    def __init__(self, msgid, korean, english):
        self.msgid = msgid
        self.english = english
        self.korean = korean

    def register(self):
        SQL = "INSERT INTO web_translations (msgid, korean, english) VALUES (%s,%s,%s);"
        parameters = (self.msgid, self.korean, self.english,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE web_translations SET msgid = %s, korean = %s, english = %s WHERE id = %s;"
        parameters = (self.msgid, self.korean, self.english, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)


class RecipeComments(Main):
    def __init__(self, productid, comment):
        self.productid = productid
        self.comment = comment

    def register(self):
        SQL = "INSERT INTO recipe_comments (productid, comment) VALUES (%s,%s);"
        parameters = (self.productid, self.comment,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE recipe_comments SET productid = %s, comment = %s WHERE id = %s;"
        parameters = (
            self.productid, self.comment, id,)
        self.execute_query(query=SQL, parameters=parameters, commit=True)
